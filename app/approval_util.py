from datetime import datetime
from dataclasses import dataclass, field
from typing import TypeVar, List

from sqlalchemy import and_

from app import db

T = TypeVar('T')
# table: T

@dataclass
class NoZeroTable(): 
    table: T
    args: list[datetime] = field(default_factory=list)

    def __select_zero_date_tables(self) -> List[T]:
        filters = []
        for arg in self.args:
            filters.append(getattr(self.table, arg)==0)
        
        datetime_query = self.table.query.filter(and_(*filters)).all()
        return datetime_query
    
    def convert_zero_to_none(self) -> None:
        pickup_objects = self.__select_zero_date_tables()

        for zero_contain_obj in pickup_objects:
            for arg in self.args:
                setattr(zero_contain_obj, arg, None)
                # print(f'Noneを期待：　{getattr(zero_contain_obj, arg)}')
                db.session.merge(zero_contain_obj)
                db.session.commit()

"""
    00:00:00の値を持つ属性を有するオブジェクトのリストを返す
    Param:
        table: T (クラステーブル)
        *args: datetime (00：00：00を持つであろう属性名)
    Return:
        datetime_query: List[T]
    """         
def select_zero_date(table: T, *args: datetime) -> List[T]:
    filters = []
    for arg in args:
        #   if arg==0:
            filters.append(arg==0)
    
    datetime_query = table.query.filter(and_(*filters)).all()
    return datetime_query

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
