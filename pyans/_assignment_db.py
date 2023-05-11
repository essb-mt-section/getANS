from __future__ import annotations

import os.path
import pickle
import re
from bz2 import BZ2File
from datetime import date
from typing import AnyStr, Iterator, List, Optional, Union

import pandas as pd

from ._ans_api import ANSApi
from ._misc import print_feedback
from .types import Assignment

api = ANSApi() # global API instance

class AssignmentDB(object):

    DB_SUFFIX = ".ansdb"

    def __init__(self):
        self.filename = None
        self._assignments = []

    @property
    def assignments(self) -> List[Assignment]:
        return self._assignments

    @assignments.setter
    def assignments(self, val: Union[Iterator[Assignment], List[Assignment]]):
        self._assignments = list(val)

    def dataframe(self, raw_dict:bool=False) -> pd.DataFrame:
        tmp = []
        for ass in self._assignments:
            df = ass.dataframe(raw_dict=raw_dict)
            tmp.append(df)
        rtn = pd.concat(tmp)
        rtn = rtn.reset_index()
        return rtn

    def results_df(self, raw_ans_data:bool=False) -> pd.DataFrame:
        tmp = []
        for ass in self._assignments:
            df = ass.results_dataframe(raw_ans_data=raw_ans_data)
            tmp.append(df)
        rtn = pd.concat(tmp)
        rtn = rtn.reset_index()
        return rtn

    def overview(self):

        n_resp = 0
        n_submissions = 0
        n_answer_details = 0
        for ass in self._assignments:
            if ass.results is not None:
                for r in ass.results:
                    n_resp += 1
                    if r.submissions is not None:
                        for s in r.submissions:
                            n_submissions += 1
                            if s.scores is not None:
                                n_answer_details += 1

        d = {"assignments": len(self._assignments),
             "responses": n_resp,
             "submissions": n_submissions,
             "answer details": n_answer_details}

        return pd.DataFrame({"types": d.keys(), "n": d.values()})

    def get_by_name(self, regexp:AnyStr,
                                and_not_regexp:Optional[AnyStr]=None) -> Iterator[Assignment]:
        match = re.compile(regexp)
        if and_not_regexp is None:
            flt_fnc = lambda x: match.search(x.dict["name"]) is not None
        else:
            not_match = re.compile(and_not_regexp)
            flt_fnc = lambda x: match.search(x.dict["name"]) is not None and \
                            not_match.search(x.dict["name"]) is None

        return filter(flt_fnc, self._assignments)

    def get_by_dict(self, key, value) -> Iterator[Assignment]:
        return filter(lambda x: x.dict[key] == value, self._assignments)

    def get_by_id(self, id) -> Iterator[Assignment]:
        return filter(lambda x: x.id == id, self._assignments)

    def save(self, filename:Optional[str]=None, override:bool=False):
        if isinstance(filename, str):
            if not filename.endswith(AssignmentDB.DB_SUFFIX):
                filename = filename + AssignmentDB.DB_SUFFIX

            if not override:
                new_filename_needed = False
                while True:
                    if os.path.isfile(filename):
                        new_filename_needed = True
                        filename = filename.removesuffix(AssignmentDB.DB_SUFFIX)
                        i = filename.rfind("_")
                        if i>=0:
                            try:
                                cnt = int(filename[i+1:]) #number at the end
                                filename = filename[:i]
                            except ValueError:
                                cnt = 0
                        else:
                            cnt = 0
                        filename = f"{filename}_{cnt+1}{AssignmentDB.DB_SUFFIX}"
                    else:
                        break # filename OK

                if new_filename_needed:
                    print(f" DB already exists. Create new database {filename}")

            self.filename = filename

        if self.filename is not None:
            with BZ2File(self.filename, 'wb') as f:
                pickle.dump(self, f, protocol=pickle.HIGHEST_PROTOCOL)


    def initialize(self,
              start_date:Union[str, date],
              end_date:Union[str, date],
              select_by_name:str,
              feedback:bool = True):

        api.init_token()
        self.assignments = api.find_assignments(start_date=start_date,
                                                end_date=end_date)
        self.assignments = self.get_by_name(select_by_name)
        # retrieve course information
        api.download_course_info(self.assignments, feedback=feedback)

    def retrieve(self,
                results = False,
                questions = False,
                submissions=False,
                answer_details=False,
                force_update = False,
                _feedback_queue=None): # TODO dealing with feedback queue
        # retrieve data if they do not exists
        api.save_callback_fnc(self.save) # save while waiting
        api.feedback_queue = _feedback_queue

        if results:
            api.download_results(self._assignments,
                                     force_update=force_update)
            self.save()

        if questions:
            api.download_exercises_and_questions(self._assignments,
                                                     force_update=force_update)
            self.save()

        if submissions:
            api.download_submissions(self._assignments,
                                        force_update=force_update)
            self.save()

        if answer_details:
            ##FIXME TODO
            self.save()


        # if answer_details:
        #     # retrieve all answer details (that takes VERY LONG)
        #     for cnt_ass, ass in enumerate(self.assignments):
        #         for cnt_res, res in enumerate(ass.results):
        #             while True:
        #                 info = "({} of {}) (assignment {} of {}, {})".format(
        #                     cnt_res + 1, len(ass.results), cnt_ass + 1,
        #                     len(self.assignments), ass.dict["name"])
        #                 try:
        #                     api.retrieve_answer_details(result=res,
        #                                                     force_update=force_update,
        #                                                     additional_feedback=info)
        #                     break
        #                 except requests.exceptions.HTTPError as err:
        #                     print_feedback(err)  # HTTP error p
        #                     sleep(15)  # wait some time and retry

        #         self.save()



def load_db(filename) -> AssignmentDB:
    print_feedback("Loading {}".format(filename))
    try:
        with BZ2File(filename, 'rb') as f:
            rtn = pickle.load(f)
    except Exception as err:
        raise IOError("Can't load database file {}".format(filename)) from err

    rtn.filename = filename
    return rtn
