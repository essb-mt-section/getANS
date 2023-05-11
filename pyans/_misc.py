import datetime
from queue import Queue
from typing import Optional

print_fnc = print

def print_feedback(text, feedback_queue: Optional[Queue]=None) -> None:
    # write also to feedback multiprocessing queue
    print_fnc(text)
    if isinstance(feedback_queue, Queue):
        feedback_queue.put(text)


def flatten(list_):
    return [elm for sublist in list_ for elm in sublist]


def make_date(data_str:str) -> datetime.date:
    formats = ["%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y"]

    while True:
        f = formats.pop()
        try:
            return datetime.datetime.strptime(data_str, f).date()
        except ValueError as err:
            if len(formats) == 0:
                raise err