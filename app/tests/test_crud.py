import pytest
import datetime

from app import db
from app.models_aprv import NotificationList

# sample_end_datetime = datetime(2023, 9, 30, 1, 1, 59)

def conv_str_date() -> str:
    sample_start_date = datetime.now().date()
    date_str = sample_start_date.strftime('%Y/%m/%d.%f')
    return date_str

def conv_str_time() -> str:
    sample_start_time = datetime.now().time()
    time_str = sample_start_time.strftime('%H:%M:%S.%f')
    return time_str

# @pytest.mark.skip
def test_sample_add_notification_data(app_context):
    notification_1 = NotificationList(30, 8,
                                      datetime.datetime.now().date(), datetime.datetime.now().time(),
                                      datetime.datetime.now().date() + datetime.timedelta(days=3),
                                      datetime.datetime.now().time(), "軒下の雪で")
    db.session.add(notification_1)
    db.session.commit()

# @pytest.mark.skip
def test_select_notification_data(app_context):
    one_notification_data = NotificationList.query.filter(NotificationList.STAFFID==20).all()
    assert len(one_notification_data) == 2