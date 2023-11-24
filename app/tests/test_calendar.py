import pytest
import datetime
from typing import Tuple

from app import db
from app.holiday_acquisition import HolidayAcquire
from app.new_calendar import NewCalendar
from app.content_paidholiday import get_holidays_area
from app.models_aprv import PaidHoliday


@pytest.fixture
def get_official_user(app_context):
    acquisition_object = HolidayAcquire(20)
    return acquisition_object


def test_convert_base_day(get_official_user):
    conv_date = get_official_user.convert_base_day()
    # print(conv_date)
    assert conv_date.month == 10


@pytest.mark.skip
def test_calcurate_days(get_official_user):
    final_data_list = get_official_user.print_date_type_list()
    print(final_data_list)


full_time = list(range(10, 12)) + list(range(12, 20, 2))  # 以降20
part_timeB = [7, 8, 9, 10, 12, 13]  # 以降15
part_timeC = [5, 6, 6, 8, 9, 10]  # 以降11
part_timeD = [3, 4, 4, 5, 6, 6]  # 以降7
part_timeE = [1, 2, 2, 2, 3, 3]  # 以降3


@pytest.mark.skip
def test_plus_2years_over_holidays(get_official_user):
    test_result_dict = get_official_user.plus_next_holidays(full_time, 20)
    print(test_result_dict)


# @pytest.mark.skip
def test_get_holiday_area(app_context):
    # print(make_user_object.STAFFID)
    holiday_info: Tuple[datetime.date, datetime.date, int] = get_holidays_area(20)
    print(holiday_info[0])


def test_insert_ph_db(app_context):
    # paid_holiday_obj = PaidHoliday(20)
    start_list, end_list, acquisition_list = get_holidays_area(20)
    # holiday_info = get_holidays_area(20)
    # for start_day, end_day, acquisition in start_list, end_list, acquisition_list:
    for value in start_list:
        print(value)


#     paid_holiday_obj.STAFFID = 20
#     paid_holiday_obj.STARTDAY = start_day
#     paid_holiday_obj.ENDDAY = end_day
#     paid_holiday_obj.paid_holiday = acquisition
#     db.session.add(paid_holiday_obj)

# db.session.commit()


# おニューカレンダーテスト
@pytest.fixture
def make_new_calendar():
    new_calendar = NewCalendar(2023, 9)
    return new_calendar


@pytest.mark.skip
def test_get_itermonthdays(make_new_calendar):
    result = make_new_calendar.get_itermonthdays()
    print(result)


@pytest.mark.skip
def test_get_month_holidays_num(make_new_calendar):
    print(make_new_calendar.__get_jp_holidays_num())


@pytest.mark.skip
def test_get_weekday(make_new_calendar):
    print(make_new_calendar.get_weekday())
