from datetime import date, datetime
from dataclasses import dataclass
from typing import List
from collections import OrderedDict
from monthdelta import monthmod
from dateutil.relativedelta import relativedelta

from app.models import User


@dataclass
class HolidayAcquire:
    id: int
    # acquisition_pair: Optional(List[OrderedDict(date, int)])

    def __post_init__(self):
        target_user = User.query.filter(User.STAFFID == self.id).first()
        self.in_day: date = target_user.INDAY

    # acquire: 日数
    # get: 日付
    def convert_base_day(self) -> date:
        # 基準月に変換
        #     入社日が4月〜9月
        #     10月1日に年休付与
        if self.in_day.month >= 4 and self.in_day.month < 10:
            change_day = self.in_day.replace(month=10, day=1)  # 基準月
            return change_day  # 初回付与日

        #     入社日が10月〜12月
        #     翌年4月1日に年休付与
        elif self.in_day.month >= 10 and self.in_day.month <= 12:
            change_day = self.in_day.replace(month=4, day=1)
            return change_day + relativedelta(months=12)

        #     入社日が1月〜3月
        #     4月1日に年休付与
        elif self.in_day.month < 4:
            change_day = self.in_day.replace(month=4, day=1)
            return change_day

    # 付与日のリストを返す（一回足りないか？）
    def calcurate_days(self, base_day: date) -> List[datetime]:
        holidays_get_list = []
        self.base_day = base_day + relativedelta(months=12)
        while base_day < datetime.today():
            holidays_get_list.append(self.base_day)
            if datetime.today() < self.base_day:
                break
            return holidays_get_list + self.calcurate_days(self.base_day)

        return holidays_get_list
        # 次回付与日
        # return holidays_get_list[-1].date()

    # ちゃんとした付与日のリストを返すdata型で
    def print_date_type_list(self) -> List[date]:
        base_day = self.convert_base_day()
        type_conv_list = [hl.date() for hl in self.calcurate_days(base_day)]
        type_conv_list.insert(0, base_day.date())
        return type_conv_list

    # おそらくこれも次回付与日を求める
    # def get_next_holiday(self):
    #     base_day = self.convert_base_day()

    #     next_acquire_day = date(date.today().year, base_day.month, 1)
    #     return next_acquire_day

    def acquire_start_holidays(self) -> OrderedDict[date, int]:
        base_day = self.convert_base_day()
        day_list = self.print_date_type_list()
        # monthmod(date.today(), base_day)[0].months < 6:
        if monthmod(self.in_day, base_day)[0].months <= 2:
            acquisition_days = 2
        elif monthmod(self.in_day, base_day)[0].months <= 3:
            acquisition_days = 1
        elif monthmod(self.in_day, base_day)[0].months > 3:
            acquisition_days = 0

        first_data = [(day_list[0], acquisition_days)]
        return OrderedDict(first_data)

    def plus_next_holidays(self) -> OrderedDict[date, int]:
        day_list = self.print_date_type_list()
        start_pair = self.acquire_start_holidays()

        acquisition_next_days = list(range(10, 12)) + list(range(12, 20, 2))
        for i, acquisition_day in enumerate(acquisition_next_days):
            if i == len(day_list):
                break
            else:
                start_pair[day_list[i + 1]] = acquisition_day

        if len(day_list) > len(acquisition_next_days):
            for day in day_list[7:]:
                start_pair[day] = 20

        return start_pair
