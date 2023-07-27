import pytest
import datetime

from app import db
from app.models_aprv import NotificationList

@pytest.fixture(name='testdb')
def connect_db():
    return db

sample_start_datetime = datetime(2023, 9, 1, 23, 59, 1)
sample_end_datetime = datetime(2023, 9, 30, 1, 1, 59)

@pytest.fixture(name='add_one')
def sample_add_notification_data(testdb):
    notification_1 = NotificationList(20, 4, 0, sample_start_datetime.date(), sample_end_datetime.date(), sample_start_datetime.time(), sample_end_datetime.time(), "ヤギが逃げたため")
    testdb.session.add(notification_1)
    testdb.session.commit()

def test_select_notification_data(add_one):
    one_notification_data = NotificationList.query.filter_by(NotificationList.STAFFID==20)
    assert one_notification_data.query.get(STATUS) == 4
