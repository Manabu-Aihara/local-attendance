from datetime import datetime
from dataclasses import dataclass, field
from typing import TypeVar, List, Callable

from sqlalchemy import and_

from app import db

T = TypeVar('T')
# table: T

@dataclass
class NoZeroTable(): 
    table: T
    # args: list[datetime] = field(default_factory=list)

    # 00:00:00が存在するオブジェクトを抽出
    def select_zero_date_tables(self, *args: datetime) -> List[T]:
        filters = []
        for arg in args:
            filters.append(getattr(self.table, arg)==0)
        
        datetime_query = self.table.query.filter(and_(*filters)).all()
        return datetime_query
    
    # 同日付が存在するオブジェクトを抽出
    def select_same_date_tables(self, *args: datetime) -> List[T]:
        filter = getattr(self.table, args[0])==getattr(self.table, args[1])
    
        datetime_query = self.table.query.filter(and_(filter)).all()
        return datetime_query

    def convert_value_to_none(self, func: Callable[[datetime, datetime], List[T]], target: list[datetime] | datetime) -> None:
        pickup_objects = func

        # print(type(target))
        # print(len(pickup_objects))
        for pickup_obj in pickup_objects:
            if type(target) is list:
                for arg in target:
                    setattr(pickup_obj, arg, None)
                    # print(f'Noneを期待：　{getattr(pickup_obj, arg)}')
                    # db.session.merge(pickup_obj)
                    # db.session.commit()
            # ここは'str'指定じゃないとダメ
            elif type(target) is str:
                setattr(pickup_obj, target, None)
                # print(f'Noneを期待：　{getattr(pickup_obj, target)}')
                # db.session.merge(pickup_obj)
                # db.session.commit()
            else:
                print('type is not both')

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
