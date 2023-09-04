from datetime import date
from monthdelta import monthmod
from dataclasses import dataclass
from typing import Tuple
from dateutil.relativedelta import relativedelta

from app.models import User

@dataclass
class HolidayAcquire:
	id: int

	def __post_init__(self):
		self.target_user = User.query.get(self.__class__.id)
		self.in_day: date = self.target_user.INDAY

	def convert_base_day(self) -> date:
		##### 基準月に変換 #####
		#     入社日が4月〜9月
		#     10月1日入社日として、10月1日に年休付与
		if self.in_day.month >= 4 and self.in_day.month < 10:
			change_day = self.in_day.replace(month=10, day=1) # 基準月
			return change_day  # 初回付与日
		
		#     入社日が10月〜12月
		#     4月1日入社日として、翌年4月1日に年休付与
		elif self.in_day.month >= 10 and self.in_day.month <= 12:
			change_day = self.in_day.replace(month=4, day=1)
			return change_day + relativedelta(months=12)
		
		#     入社日が1月〜3月
		#     4月1日入社日として、4月1日に年休付与
		elif self.in_day.month < 4:
			change_day = self.in_day.replace(month=4, day=1)
			return change_day
	
	def calcurate_days(self, base_day: date) -> Tuple[date]:
		# 12ヶ月ごとに付与される？→self.base_dayはリストじゃないか？
		while base_day < date.today():
			self.base_day = base_day + relativedelta(months=12)

		last_given_day = self.base_day - relativedelta(months=12)  # 今回付与
		next_given_day = self.base_day  # 次回付与

		return (last_given_day, next_given_day)
										
	def acquire_holiday(self):
		self.given_holidays = []

		base_day = self.convert_base_day()
		if date.today() < base_day and monthmod(date.today(), base_day)[0].months < 6:
			self.given_holidays.append(self.inday)  # 今回付与
			self.given_holidays(base_day)  # 次回付与
		elif date.today() > base_day and monthmod(base_day, date.today())[0].months < 6:
			given_days = self.calcurate_days(base_day)
			return given_days
		else:
			given_days = self.calcurate_days(base_day)
			return given_days
			