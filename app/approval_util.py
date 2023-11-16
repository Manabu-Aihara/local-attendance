from datetime import datetime
from dataclasses import dataclass
from typing import TypeVar, List, Callable, Union
import numpy

from sqlalchemy import or_


T = TypeVar("T")
# table: T


@dataclass
class NoZeroTable:
    table: T
    # args: list[datetime] = field(default_factory=list)

    """
    00:00:00が存在するオブジェクトを抽出
    Param:
        table: T (クラステーブル)
        *args: datetime (00：00：00を持つであろう属性名)
    Return:
        datetime_query: List[T]
    """

    def select_zero_date_tables(self, *args: datetime) -> List[T]:
        filters = []
        for arg in args:
            filters.append(getattr(self.table, arg) == 0)

        datetime_query = self.table.query.filter(or_(*filters)).all()
        return datetime_query

    # 同日付が存在するオブジェクトを抽出
    # def select_same_date_tables(self, *args: datetime) -> List[T]:
    #     filter = getattr(self.table, args[0])==getattr(self.table, args[1])

    #     datetime_query = self.table.query.filter(and_(filter)).all()
    #     return datetime_query

    def convert_value_to_none(
        self, func: Callable[[datetime, datetime], List[T]], *target: str
    ) -> None:
        pickup_objects = func

        for pickup_obj in pickup_objects:
            for one_val in target:
                if getattr(pickup_obj, one_val).strftime("%H:%M:%S") == "00:00:00":
                    setattr(pickup_obj, one_val, None)
                    # print(f'Noneを期待：　{getattr(pickup_obj, one_val)}')
                # db.session.merge(pickup_obj)
                # db.session.commit()


"""
datetimeをdate型にするクラス（引数カラム名なしで）
"""


@dataclass
class DateConvertTable:
    table: T
    U = TypeVar("U")

    # datetime型のカラム名を取得
    def search_datetime_type(self, U) -> List[str]:
        columns = dir(self.table)
        # 一行目だけ抽出し、列の型リストを取得
        one_instance = self.table.query.first()
        column_list: List[str] = [
            c for c in columns if type(getattr(one_instance, c)) is U
        ]

        return column_list

    # search_datetime_typeより、datetimeデータを取得
    def get_datetime(self) -> List[U]:
        # TypeError: search_datetime_type() missing 1 required positional argument: 'self'
        # target_column_list = func(self)
        target_column_list = self.search_datetime_type(datetime)
        target_date_list = []
        for target_column in target_column_list:
            # こちらはgetattr(クラス,)...不思議
            target_date_list.append(
                self.table.query.with_entities(getattr(self.table, target_column)).all()
            )

        np_date_list = numpy.array(target_date_list)
        # 多次元配列を一次元に変換
        return np_date_list.flatten()

    def convert_to_date(self) -> List[datetime.date]:
        datetime_list = self.get_datetime()
        date_result_list = [dl.date() for dl in datetime_list if dl is not None]
        return date_result_list


def toggle_notification_type(table, arg: Union[str, int]) -> Union[int, str]:
    # 数値を内容名に置き換える
    if type(arg) is int:
        content_value = table.query.get(arg)
        return content_value.NAME
    # 内容名を数値に置き換える
    elif type(arg) is str:
        content_value = table.query.filter(table.NAME == arg).first()
        return content_value.CODE
    else:
        raise TypeError("intかstrのどちらかです")
