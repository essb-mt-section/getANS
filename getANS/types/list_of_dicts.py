from typing import Any, List, Tuple, Union
import pandas as pd  # install also tabulate

NESTED_KEY_SEPARATOR = "/"


'''
nested dicts
'''

def nested_value(nested_dict: dict, nested_key: Union[str, List[str], Tuple[str]]):
    if isinstance(nested_key, str):
        nested_key = nested_key.split(NESTED_KEY_SEPARATOR)
    elif not isinstance(nested_key, (list, tuple)):
        raise TypeError("nested_key has to be a string, list or tuple")
    rtn = nested_dict
    for k in nested_key:
        try:
            rtn = rtn[k]
        except KeyError:
            return None
    return rtn


def nested_keys(nested_dict: dict):
    keys = []
    for k in nested_dict.keys():
        if isinstance(nested_dict[k], dict):
            for k2 in nested_keys(nested_dict[k]):
                keys.append("{}{}{}".format(k, NESTED_KEY_SEPARATOR, k2))
        else:
            keys.append(k)
    return keys


'''
list of dicts
'''


def find(list_of_dict: List[dict], key: Any, value: Any) -> list:
    rtn = []
    for d in list_of_dict:
        try:
            if d[key] == value:
                rtn.append(d)
        except KeyError:
            continue
    return rtn


def keys(list_of_dict: List[dict], nested:bool=False) -> list:
    keys = set()
    for d in list_of_dict:
        if nested:
            keys.update(nested_keys(d))
        else:
            keys.update(d.keys())
    return list(keys)


def values(list_of_dict: List[dict], key:Any, nested:bool=False) -> list:
    # dicts key uses slashes for next level keys
    rtn = []
    for d in list_of_dict:
        if nested:
            rtn.append(nested_value(d, key))
        else:
            try:
                rtn.append(d[key])
            except KeyError:
                rtn.append(None)
    return rtn


def dataframe_from_list_of_dict(list_of_dict, columns=None, nested: bool = False):
    # get values from list of dict
    if columns is None:
        columns = list(keys(list_of_dict, nested=nested))

    if not isinstance(columns, (list, tuple)):
        columns = [columns]

    rtn = {}
    for k in columns:
        rtn[k] = values(list_of_dict, k, nested=nested)

    return pd.DataFrame(rtn)

