import datetime
import logging
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


def init_logging():
        log_file = "retrieval.log"
        logging.basicConfig(level=logging.INFO,
                        format='[%(asctime)s]  %(message)s',
                        datefmt='%m-%d %H:%M:%S',
                        filename=log_file,
                        filemode='a')
        print("Log file: {}".format(log_file))

# logging.warning(l)
# logging.error(l)
# logging.info(l)


def move_column_to_front(df, column_name):
    """
    Moves the specified column to the first position in the DataFrame.

    Parameters:
    df (pd.DataFrame): The DataFrame to modify.
    column_name (str): The name of the column to move.

    Returns:
    pd.DataFrame: A new DataFrame with the column moved to the first position.
    """
    if column_name not in df.columns:
        raise ValueError(f"Column '{column_name}' not found in DataFrame")

    return df[[column_name] + [col for col in df.columns if col != column_name]]
