import itertools
from collections.abc import Callable
from datetime import date, timedelta
from json.decoder import JSONDecodeError
from multiprocessing import Pool
from time import sleep, time
from typing import Dict, List, Optional, Union

from . import _request_tools as rt
from . import token
from ._misc import flatten, make_date, print_feedback
from .types import Assignment, Course, Exercise, Question, Result, Submission

DEFAULT_N_THREADS = 20

class ANSApi(object):

    URL = "https://ans.app/api/v2/"
    N_REQUESTS_PER_MINUTE  = 495 #TODO could be moved to initialize
    SAVE_INTERVALL = 10

    def __init__(self, n_threads:int = DEFAULT_N_THREADS):
        self._save_callback_fnc = None
        self.__auth_header = None
        self._n_threads = 1
        self.feedback_queue = None
        self._request_history = rt.TimeStampHistory(ANSApi.N_REQUESTS_PER_MINUTE)
        self.cache = rt.Cache()

        self.n_threads  = n_threads
        self.init_token()

    @property
    def n_threads(self) -> int:
        return self._n_threads

    @n_threads.setter
    def n_threads(self, val:int):
        if val < 1:
            val = 1
        self._n_threads = val

    def init_token(self):
        try:
            token_str = token.read()
        except RuntimeError:
            self.__auth_header = None
            return
        self.__auth_header = {"Authorization":
                              "Token token={}".format(token_str)}

    @property
    def has_token(self):
        return self.__auth_header is not None

    def _check_token(self):
        if self.__auth_header is None:
            raise RuntimeError(token.NO_TOKEN_ERROR_MSG)


    @staticmethod
    def make_url(what, query_txt="",
                  page:Optional[int]=None,
                  items:Optional[int]=100) -> str:
        """if getting multiple items (see ANS API doc) define items and page
        """
        if isinstance(items, int) and isinstance(page, int):
            what = what + f"?items={items}&page={page}"

        url = ANSApi.URL + what
        if len(query_txt):
            if url.find("?")>0:
                # question separator already in url -> use &
                sep = "&"
            else:
                sep = "?"
            url = url + sep + "query=" + query_txt

        return url

    def save_callback_fnc(self, fnc):
        self._save_callback_fnc = fnc

    def _save(self):
        # intermediate save, if save_callback_fnc is defined
        if isinstance(self._save_callback_fnc, Callable):
            self._save_callback_fnc()

    def _register_and_delay(self):
        """register online request and delays process if required due to overfull history"""
        # prepares access and wait if required
        crit_time = timedelta(seconds=60)
        if self._request_history.is_full() and \
                        self._request_history.lag(0) <= crit_time:
            self._save()
            tmp =  crit_time - self._request_history.lag(0)
            wait_time = tmp.seconds +1
            self._request_history.history = []
            self._feedback(f"Request limit of {self._request_history.max_size} reached. Waiting {wait_time} seconds...")
            sleep(wait_time)

        self._request_history.timestamp() # register upcoming


    def get(self, url) -> Union[Dict, None, List[Dict]]:
        """Returns the requested response or None

        Function delays if required.
        """
        self._check_token()
        self._register_and_delay()
        rtn = rt.request_json(url, headers=self.__auth_header)
        if rtn is not None:
            self.cache.add(url, rtn)
        return rtn

    def get_multiple_pages(self, what, query_txt:str="",
                           items:int=100,
                           start_page_counter:int=1) -> List[Dict]:
        """Returns the result of a multiple pages request
            - all pages (from start cnt) of a multiple item request

        Might return [], if nothing received

        Sequentially calls all pages and quits if last page is received.
        Function delays if required

        Note: Use make_url and get(url), if you need a particular page
        """

        self._check_token()
        rtn_lists = []
        page_cnt = start_page_counter -1

        while True:
            page_cnt = page_cnt + 1
            url = ANSApi.make_url(what=what, items=items, page=page_cnt,
                                 query_txt=query_txt)

            new_list = self.cache.get(url)
            if new_list is None:
                # retrieve online
                new_list = self.get(url)

            if new_list is None or len(new_list)==0:
                break # end request loop, because nothing received
            else:
                if new_list in rtn_lists :
                    break # end request loop, because new list has already been received

                rtn_lists.append(new_list)
                if len(new_list) < items:
                    break # end request loop, because less items than requested

        return flatten(rtn_lists)


    def find_assignments(self,
                         start_date:Union[str, date],
                         end_date:Union[str, date]) -> List[Assignment]:
        oneday = timedelta(days=1)
        if not isinstance(start_date, date):
            start_date = make_date(start_date)
        if not isinstance(end_date, date):
            end_date = make_date(end_date)

        period = f"start_at>'{start_date - oneday}' start_at<'{end_date + oneday}'"

        self._feedback(f"retrieving assignments: {period}")

        assignments = self.get_multiple_pages(what="search/assignments",
                                   query_txt=period)
        self._feedback("  found {} assignments".format(len(assignments)))
        return [Assignment(d) for d in assignments]


    def download_course_info(self, assignments:Union[Assignment, List[Assignment]],
                                feedback=True)-> None:
        if isinstance(assignments, Assignment):
            assignments = [assignments] #force list
        # make urls
        urls = []
        for ass in assignments:
                cid = ass.dict["course_id"] # type: ignore
                urls.append(ANSApi.make_url(what=f"courses/{cid}"))

        responses = self._get_multiprocessing(urls)

        fcnt = 0
        l = len(assignments)
        for ass, rsp in zip(assignments, responses):
            ass.course= Course(rsp)
            if feedback:
                fcnt = fcnt + 1
                self._feedback(f" ({fcnt}/{l}) {ass.formated_label()}")

    def download_results(self, assignments:Union[Assignment, List[Assignment]],
                        force_update:bool=False) -> None:

        # downloads results and writes it to assignment
        if isinstance(assignments, Assignment):
            assignments = [assignments] #force list

        if not force_update:
            # filter list (only those without responses)
            assignment_list = [ass for ass in assignments if ass.results_undefined ]
        else:
            assignment_list = assignments

        # what list
        what_list = []
        feedback_list = []
        for ass in assignment_list:
            what_list.append(f"assignments/{ass.id}/results")
            feedback_list.append("[results] {}".format(ass.dict["name"]))

        chunck_size = 100
        i = 0
        while True:
            j = i + chunck_size
            responses = self._get_multiprocessing_multipages(
                                    what_list=what_list[i:j],
                                    items=100,
                                    feedback_list=feedback_list[i:j])

            for ass, rsp in zip(assignment_list[i:j], responses):
                ass.results = [Result(obj) for obj in rsp]
            self._save()
            i = j
            if i > len(assignment_list)-1:
                break


    def download_exercises_and_questions(self,
                                assignments:Union[Assignment, List[Assignment]],
                                force_update:bool=False)-> None:
        # downloads results and writes it to assignment
        if isinstance(assignments, Assignment):
            assignments = [assignments] #force list

        if not force_update:
            # filter list (only those without responses)
            assignment_list = [ass for ass in assignments if len(ass.exercises) == 0]
        else:
            assignment_list = assignments

        last_save = time()
        for ass in assignment_list:
            r = self.get_multiple_pages(what=f"assignments/{ass.id}/exercises")
            if len(r):
                self._feedback("[questions {}] {}".format(len(r), ass.dict["name"]))
                ass.exercises = [Exercise(obj) for obj in r]
                self._download_questions(ass.exercises) # multi thread
            if time() -last_save > ANSApi.SAVE_INTERVALL:
                self._save()
                last_save = time()

    def _download_questions(self, exercises:Union[Exercise, List[Exercise]]):
        if isinstance(exercises, Exercise):
            exercises = [exercises] #force list
        urls = []
        for obj in exercises:
            urls.append(ANSApi.make_url(
                            what=f"exercises/{obj.id}/questions",
                            items=50, page=1)) # should be enough questions per exercise
        responses = self._get_multiprocessing(urls)
        for obj, rsp in zip(exercises, responses):
            obj.questions = [Question(obj) for obj in rsp]


    def download_submissions(self, assignments:Union[Assignment, List[Assignment]],
                                         force_update:bool=False)-> None:
        # downloads result submissions
        if isinstance(assignments, Assignment):
            assignments = [assignments] #force list

        #collect all incomplete results make urls and feedback
        result_list = []
        feedback_list = []
        urls = []
        for cnt_ass, ass in enumerate(assignments):
            for cnt_res, res in enumerate(ass.results):
                if force_update or res.submissions_undefined:
                    result_list.append(res)
                    urls.append(ANSApi.make_url(what=f"results/{res.id}"))
                    feedback_list.append(
                        f"assignment {cnt_ass+1}/{len(assignments)}" + \
                        f" - result {cnt_res+1}/{len(ass.results)}")
        for i, fb in enumerate(feedback_list):
            feedback_list[i] = f"[result submissions] {i}/{len(feedback_list)} " + fb

        chunck_size = 100
        i = 0
        while True:
            j = i + chunck_size
            responses = self._get_multiprocessing(urls[i:j], feedback_list[i:j])
            for res, rsp in zip(result_list[i:j], responses):
                res.update(rsp)
            self._save()
            i = j
            if i > len(result_list)-1:
                break


    def downland_answer_details(self, result, force_update=False,
                                additional_feedback="")-> None: #FIXME UPdate to new method
        assert isinstance(result, Result)
        if not force_update and result.has_answer_details():
            return

        # get submission details (which answer) parallel
        self._feedback("[answer details] {} {}".format(result.id, additional_feedback))
        urls = [ANSApi.make_url(what="submissions/{}".format(s["id"])) \
                        for s in result.dict["submissions"]]
        self._register_and_delay()
        headers = [self.__auth_header] * len(urls)
        submission_dicts = []
        for r in Pool().map(rt.map_get_fnc, zip(urls, headers)):
            try:
                submission_dicts.append(r.json())
            except JSONDecodeError:
                r.raise_for_status()

        result.submissions = [Submission(obj) for obj in submission_dicts]

    def _get_multiprocessing(self, url_list:List[str],
                                    feedback_list:Optional[List[Optional[str]]]=None):
        # helper function to download from ANS
        # returns response that belong to the url_list

        self._check_token()
        rtn = []
        if feedback_list is None:
            feedback = itertools.cycle([None])
        else:
            feedback = feedback_list

        if self._n_threads<2:
            # single thread
            for url, fb in zip(url_list, feedback):
                rsp = self.cache.get(url)
                if rsp is None:
                    # try retrieve online
                    rsp = self.get(url)
                if rsp is not None and len(rsp):
                    rtn.append(rsp)
                    if fb is not None:
                        self._feedback(fb)
        else:
            # multi thread
            proc_manager = rt.RequestProcessManager(self.cache,
                                             max_processes=self._n_threads)
            rtn_dict = {} # use dict, because response come in unpredicted order
            i = -1
            for url, fb in zip(url_list, feedback):
                i = i+1
                rsp = self.cache.get(url)
                if fb is not None:
                    self._feedback(fb)
                if rsp is None:
                    # try retrieve online (add the thread list)
                    self._register_and_delay()
                    proc_manager.add(who=i,
                        thread=rt.RequestProcess(url, headers=self.__auth_header))
                else:
                    # from cache
                    rtn_dict[i] = rsp

                # read responses from threads
                while True:
                    for who, rsp in proc_manager.get_finished():
                        if rsp is not None:
                            rtn_dict[who] = rsp

                    if i < len(url_list)-1:
                        # always break, but for the last one (else)
                        # ensure that all threads are read before breaking
                        break
                    elif proc_manager.n_threads() == 0:
                        break

            # return list with correctly ordered responses
            rtn = []
            for i in range(len(url_list)):
                rtn.append(rtn_dict[i])

        return rtn

    def _get_multiprocessing_multipages(self, what_list:List[str],
                                        items:int=100,
                                        feedback_list:Optional[List[Optional[str]]]=None):
        # helper function to download from ANS
        # returns response that belong to the url_list

        self._check_token()
        rtn = []
        if feedback_list is None:
            feedback = itertools.cycle([None])
        else:
            feedback = feedback_list

        if self._n_threads<2:
            # single thread
            for what, fb in zip(what_list, feedback):
                rsp = self.get_multiple_pages(what=what, items=items)
                if rsp is not None and len(rsp):
                    rtn.append(rsp)
                    if fb is not None:
                        self._feedback(fb)
        else:
            # multi thread
            proc_manager = rt.RequestProcessManager(self.cache,
                                             max_processes=self._n_threads)
            rtn_dict = {} # use dict, because response come in unpredicted order
            i = -1
            for what, fb in zip(what_list, feedback):
                i = i + 1
                url = self.make_url(what=what) + f"?items={items}" + "&page={{cnt:1}}"
                rsp = self.cache.get(url)
                if fb is not None:
                    self._feedback(fb)
                if rsp is None:
                    # try retrieve online (add the thread list)
                    self._register_and_delay()
                    proc_manager.add(who=i,
                        thread=rt.MultiplePagesRequestProcess(url, headers=self.__auth_header))
                else:
                    # from cache
                    rtn_dict[i] = rsp

                # read responses from threads
                while True:
                    for who, rsp in proc_manager.get_finished():
                        if rsp is not None:
                            rtn_dict[who] = rsp

                    if i < len(what_list)-1:
                        # always break, but for the last one (else)
                        # ensure that all threads are read before breaking
                        break
                    elif proc_manager.n_threads() == 0:
                        break

            # return list with correctly ordered responses
            rtn = []
            for i in range(len(what_list)):
                rtn.append(rtn_dict[i])

        return rtn


    def _feedback(self, txt:str):
         print_feedback(txt, self.feedback_queue)