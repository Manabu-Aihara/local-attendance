import pytest
from datetime import date
from app.holiday_acquisition import HolidayAcquire
from app.new_calendar_class import print_monthrange

@pytest.fixture
def get_official_user(app_context):
  acquisition_object = HolidayAcquire(20)
  return acquisition_object

def test_convert_base_day(get_official_user):
  conv_date = get_official_user.convert_base_day()
  # print(conv_date)
  assert conv_date.month == 10

def test_calcurate_days(get_official_user):
  conv_date: date = get_official_user.convert_base_day()
  test_date1: date = get_official_user.calcurate_days(conv_date)
  test_date2: date = get_official_user.get_next_holiday()
  assert test_date1 == test_date2
