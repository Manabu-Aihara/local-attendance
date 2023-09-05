import pytest

from app.holiday_acquisition import HolidayAcquire

@pytest.fixture
def get_official_user(app_context):
  acquisition_object = HolidayAcquire(20)
  return acquisition_object

def test_convert_base_day(get_official_user):
  conv_date = get_official_user.convert_base_day()
  # print(conv_date)
  assert conv_date.month == 10

def test_calcurate_days(get_official_user):
  conv_date = get_official_user.convert_base_day()
  get_official_user.calcurate_days(conv_date)
