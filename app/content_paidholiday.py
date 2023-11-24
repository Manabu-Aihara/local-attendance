from typing import Tuple
from datetime import date, time
from monthdelta import monthmod
from dateutil.relativedelta import relativedelta

from app.holiday_acquisition import HolidayAcquire
from app.models_aprv import NotificationList


# 個別申請リストページへ
def get_holidays_area(staff_id: int) -> Tuple[list[date], list[date], list[int]]:
    full_time = list(range(10, 12)) + list(range(12, 20, 2))  # 以降20

    holidays_print_obj = HolidayAcquire(staff_id)
    # 取得日、日数のペア
    holiday_dict = holidays_print_obj.plus_next_holidays(full_time, 20)

    end_day_list = [end_day + relativedelta(days=-1) for end_day in holiday_dict.keys()]
    end_day_list[0] = None

    return (
        list(holiday_dict.keys()),
        end_day_list,
        list(holiday_dict.values()),
    )


def get_sum_rests(id: int, base_times: int) -> time:
    start_day, end_day, start_time, end_time = (
        NotificationList.query.with_entities(
            NotificationList.START_DAY,
            NotificationList.END_DAY,
            NotificationList.START_TIME,
            NotificationList.END_TIME,
        )
        .filter(NotificationList.id == id)
        .first()
    )
    calcurate_times: time = int(monthmod(start_day, end_day)) * base_times
    calcurate_times += monthmod(start_time, end_time)
    return calcurate_times


def decrement_stock(staff_id: int, notification_id: int) -> Tuple[int, int]:
    holiday_list = get_holidays_area(staff_id)[2]

    default_sum_holiday = (
        sum(holiday_list[-4:-2]) if len(holiday_list) >= 4 else sum(holiday_list[:-2])
    )
