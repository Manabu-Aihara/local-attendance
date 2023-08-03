from datetime import datetime
from typing import TypeVar, List

from app.models_aprv import NotificationList

# class OutputApprovalDataConversion():
    
def convert_str_to_date(arg: datetime) -> datetime:
    if arg != '':
        return arg
    else:
        conv_date_empty = arg.replace('%Y-%m-%d', '')
        return conv_date_empty

def convert_str_to_time(arg: datetime) -> datetime:
    if arg != '':
        return arg
    else:
        conv_time_empty = arg.replace('%H:%M', '')
        return conv_time_empty
    
def toggle_notification_type(table, arg: str | int) -> int | str:
    # 数値を内容名に置き換える
    if type(arg) is int:
        content_value = table.query.get(arg)
        return content_value.NAME
    elif type(arg) is str:
        content_value = table.query.filter(table.NAME==arg).first()
        return content_value.CODE
    else:
        TypeError("intかstrのどちらかです")

T = TypeVar('T')
def search_uneffective_time_index(list_obj) -> list[int]:
    list_obj.attribute_time: datetime
    return [i for i, x in enumerate(list_obj) if x.START_TIME.strftime('%H:%M:%S') == "00:00:00"]

def replace_uneffective_index_time(list_obj: list[T]) -> list[str]:
    index: list = search_uneffective_time_index(list_obj)
    for i in index:
        list_obj[i].START_TIME = _replace(list_obj[i])
        return list_obj[i].START_TIME.strftime('')

def _replace(t_object: T) -> datetime:
    zero_date_mod: str = t_object.START_TIME.strftime('%H:%M:%S').replace("00:00:00", "")
    zero_date = datetime.strptime(zero_date_mod, "")
    return zero_date

def except_zero_time(zero_time: datetime) -> datetime:
    time_replace_str: str = zero_time.strftime('').replace("00:00:00", "No!")
    time_replace: datetime = datetime.strptime(time_replace_str, '')
    return time_replace

def convert_object_time(*args: list[datetime]) -> T:
    object_t = T
    for arg in args:
        object_t.arg = except_zero_time(arg)

    return object_t

def insert_out_index(list_obj: list[T]) -> list[T]:
    list_modify = []
    index: list[int] = search_uneffective_time_index(list_obj)
    for i in index:
        list_modify.insert(i, convert_object_time)