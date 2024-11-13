from __future__ import annotations

import os.path
import pickle
import re
from bz2 import BZ2File
from datetime import date
from typing import AnyStr, Iterator, List, Optional, Union

import pandas as pd

from . import _ans_api
from ._misc import print_feedback
from .types import Assignment, Course

api = _ans_api.ANSApi()  # global API instance


class AssignmentDB(object):

    DB_SUFFIX = ".ansdb"

    def __init__(self, info=""):
        self.filename = None
        self._assignments = []
        self.info = info

    @property
    def assignments(self) -> List[Assignment]:
        return self._assignments

    @assignments.setter
    def assignments(self, val: Union[Iterator[Assignment], List[Assignment]]):
        self._assignments = list(val)

    def dataframe(self, raw_dict: bool = False) -> pd.DataFrame:
        tmp = []
        for ass in self._assignments:
            df = ass.dataframe(raw_ans_data=raw_dict)
            tmp.append(df)
        rtn = pd.concat(tmp)
        rtn = rtn.reset_index().drop(columns=["index"])
        return rtn

    def course_list_df(self):
        names = []
        codes = []

        for ass in self._assignments:
            if isinstance(ass.course, Course):
                code = ass.course.course_code
                name = ass.course.name
                if code not in codes:
                    codes.append(code)
                    names.append(name)

        return pd.DataFrame({"code": codes,
                             "name": names})

    def grades_df(self, raw_ans_data: bool = False) -> pd.DataFrame:
        tmp = []
        for ass in self._assignments:
            df = ass.grades_dataframe(raw_ans_data=raw_ans_data)
            tmp.append(df)
        rtn = pd.concat(tmp)
        rtn = rtn.reset_index().drop(columns=["index"])
        return rtn

    def assignments_df(self, raw_ans_data: bool = False) -> pd.DataFrame:
        tmp = []
        for ass in self._assignments:
            df = ass.dataframe(raw_ans_data=raw_ans_data)
            tmp.append(df)
        rtn = pd.concat(tmp)
        rtn = rtn.reset_index().drop(columns=["index"])

        return rtn

    def submissions_df(self, n_choices: int = 0) -> pd.DataFrame:
        rtn = [ass.submissions_dataframe(n_choices)
               for ass in self._assignments]
        return pd.concat(rtn, axis=0, ignore_index=True)

    def questions_df(self) -> pd.DataFrame:
        tmp = []
        for ass in self._assignments:
            df = ass.questions_dataframe()
            tmp.append(df)
        rtn = pd.concat(tmp)
        rtn = rtn.reset_index().drop(columns=["index"])

        return rtn

    def overview(self):

        n_resp = 0
        n_submissions = 0
        n_exercises = 0
        n_questions = 0
        n_scores = 0
        for ass in self._assignments:
            if ass.results is not None:
                for r in ass.results:
                    n_resp += 1
                    if r.submissions is not None:
                        for s in r.submissions:
                            n_submissions += 1
                            if s.has_scores():
                                n_scores += 1

                for ex in ass.exercises:
                    n_exercises += 1
                    n_questions += len(ex.questions)

        d = {"assignments": len(self._assignments),
             "responses": n_resp,
             "exercises": n_exercises,
             "questions": n_questions,
             "submissions": n_submissions,
             "scores": n_scores
             }

        return pd.DataFrame({"types": d.keys(), "n": d.values()})

    def get_by_name(self, regexp: AnyStr,
                    and_not_regexp: Optional[AnyStr] = None) -> Iterator[Assignment]:
        match = re.compile(regexp)
        if and_not_regexp is None:
            def flt_fnc(x): return match.search(x.dict["name"]) is not None
        else:
            not_match = re.compile(and_not_regexp)
            def flt_fnc(x): return match.search(x.dict["name"]) is not None and \
                not_match.search(x.dict["name"]) is None

        return filter(flt_fnc, self._assignments)

    def get_by_dict(self, key, value) -> Iterator[Assignment]:
        return filter(lambda x: x.dict[key] == value, self._assignments)

    def get_by_id(self, id) -> Iterator[Assignment]:
        return filter(lambda x: x.id == id, self._assignments)

    def save(self, filename: Optional[str] = None, override: bool = False):
        if isinstance(filename, str):
            if not filename.endswith(AssignmentDB.DB_SUFFIX):
                filename = filename + AssignmentDB.DB_SUFFIX

            if not override:
                new_filename_needed = False
                while True:
                    if os.path.isfile(filename):
                        new_filename_needed = True
                        filename = filename.removesuffix(
                            AssignmentDB.DB_SUFFIX)
                        i = filename.rfind("_")
                        if i >= 0:
                            try:
                                cnt = int(filename[i+1:])  # number at the end
                                filename = filename[:i]
                            except ValueError:
                                cnt = 0
                        else:
                            cnt = 0
                        filename = f"{filename}_{cnt+1}{AssignmentDB.DB_SUFFIX}"
                    else:
                        break  # filename OK

                if new_filename_needed:
                    print(
                        f" DB already exists. Create new database {filename}")

            self.filename = filename

        if self.filename is not None:
            with BZ2File(self.filename + "~", 'wb') as f:
                pickle.dump(self, f, protocol=pickle.HIGHEST_PROTOCOL)
            try:
                os.remove(self.filename)
            except FileNotFoundError:
                pass
            os.rename(self.filename + "~", self.filename)

    def initialize(self,
                   start_date: Union[str, date],
                   end_date: Union[str, date],
                   select_by_name: str,
                   feedback: bool = True):
        """select_by_name: regular expression"""
        api.init_token()
        self.assignments = api.find_assignments(start_date=start_date,
                                                end_date=end_date)
        self.assignments = self.get_by_name(select_by_name)
        # retrieve course information
        api.download_course_info(self.assignments, feedback=feedback)

    def retrieve(self,
                 results=False,
                 exercises=False,
                 submissions=False,
                 scores=False,
                 force_update=False,
                 _feedback_queue=None):  # TODO dealing with feedback queue for GUI
        # retrieve data if they do not exists
        api.save_callback_fnc(self.save)  # save while waiting
        api.feedback_queue = _feedback_queue

        print("Retrieving missing data")
        new_data = False
        if results:
            print("-  results")
            new_data = new_data | api.download_results(
                    self._assignments, force_update=force_update)
            new_data = new_data | api.download_assignment_insights(
                    self._assignments, force_update=force_update)

        if exercises:
            print("-  exercises")
            new_data = new_data | api.download_exercises_and_questions(
                    self._assignments, force_update=force_update)
            new_data = new_data | api.download_question_insights(
                    self._assignments, force_update=force_update)

        if submissions:
            print("-  submissions")
            new_data = new_data | api.download_submissions_and_student_info(
                    self._assignments, force_update=force_update)

        if scores:
            print("-  scores")
            new_data = new_data | api.downland_scores(
                    self._assignments, force_update=force_update)

        if new_data:
            self.save()


def load_db(filename) -> AssignmentDB:
    print_feedback("Loading {}".format(filename))
    try:
        with BZ2File(filename, 'rb') as f:
            rtn = pickle.load(f)
    except Exception as err:
        raise IOError("Can't load database file {}".format(filename)) from err

    rtn.filename = filename
    return rtn
