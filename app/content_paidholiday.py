from typing import Tuple
from datetime import time
from monthdelta import monthmod

from dataclasses import dataclass

from app.holiday_acquisition import HolidayAcquire, AcquisitionType
from app.models_aprv import NotificationList


@dataclass
class HolidayCalcurate:
    # 勤務時間
    job_time: int
    # 勤務形態 Acqisition.full_timeといった形式で指定
    work_type: AcquisitionType

    """
    勤務時間に応じた、申請時間を計算
    @Param
        notification_id: int
    @Return
        calcurate_time: time
    """

    def get_sum_rests(self, notification_id: int) -> time:
        start_day, end_day, start_time, end_time = (
            NotificationList.query.with_entities(
                NotificationList.START_DAY,
                NotificationList.END_DAY,
                NotificationList.START_TIME,
                NotificationList.END_TIME,
            )
            .filter(NotificationList.id == notification_id)
            .first()
        )
        calcurate_times: time = int(monthmod(start_day, end_day)) * self.job_times
        calcurate_times += monthmod(start_time, end_time)
        return calcurate_times

    def decrement_stock(self, staff_id: int) -> Tuple[int, int]:
        acquisition_holiday_obj = HolidayAcquire(staff_id)
        holiday_dict = acquisition_holiday_obj.plus_next_holidays(self.work_type)
        holiday_list = []
        for holiday in holiday_dict.values():
            holiday_list.append(holiday)

        default_sum_holiday = (
            sum(holiday_list[-4:-1])
            if len(holiday_list) >= 4
            else sum(holiday_list[:-1])
        )
        return default_sum_holiday * self.job_time
