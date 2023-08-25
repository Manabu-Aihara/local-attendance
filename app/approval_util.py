from datetime import datetime
from dataclasses import dataclass
from typing import TypeVar, List

from sqlalchemy import and_

T = TypeVar('T')
table: T

@dataclass
class TableMatch():    
    datetime_value_list: List[datetime]

    @classmethod
    def select_zero_date_tables(cls, table: T):
        filters = []
        for date_value in cls.datetime_value_list:
                filters.append(date_value==0)
        
        datetime_query = table.query.filter(and_(*filters)).all()
        return datetime_query
         
def select_zero_date(table: T, *args: datetime) -> List[T]:
    filters = []
    for arg in args:
        #   if arg==0:
            filters.append(arg==0)
    
    datetime_query = table.query.filter(and_(*filters)).all()
    return datetime_query

# def convert_zero_to_none(select_func: List[T] = select_zero_date):
#       zero_contain_query = select_func
#       select_zero_date.__getattribute__
    
def toggle_notification_type(table, arg: str | int) -> int | str:
    # 数値を内容名に置き換える
    if type(arg) is int:
        content_value = table.query.get(arg)
        return content_value.NAME
    # 内容名を数値に置き換える
    elif type(arg) is str:
        content_value = table.query.filter(table.NAME==arg).first()
        return content_value.CODE
    else:
        raise TypeError("intかstrのどちらかです")
