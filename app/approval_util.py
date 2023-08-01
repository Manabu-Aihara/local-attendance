from datetime import datetime
from typing import TypeVar

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

def search_uneffective_time_index(list_obj):
    return [i for i, x in enumerate(list_obj) if x.START_TIME.strftime('%H:%M') == "00:00"]

T = TypeVar('T')
def replace_uneffective_index_time(list_obj: list[T]) -> list[str]:
    index: list = [i for i, x in enumerate(list_obj) if x.START_TIME.strftime('%H:%M') == "00:00"]
    for i in index:
        list_obj[i].START_TIME = _replace(list_obj[i])
        return list_obj[i].START_TIME.strftime('')

def _replace(t_object: T) -> datetime:
    zero_date_mod: str = t_object.START_TIME.strftime('%H:%M:%S').replace("00:00:00", "")
    zero_date = datetime.strptime(zero_date_mod, "")
    return zero_date
