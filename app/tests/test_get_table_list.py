import pytest
from datetime import datetime

from app.common_func import GetPullDownList
from app.models import Todokede
from app.models_aprv import NotificationList
from app.routes_approvals import get_notification_list
from app.approval_util import (toggle_notification_type,
                               convert_object_time)

@pytest.mark.skip
def test_get_notificatin_list(app_context):
    # todokede_list = GetPullDownList(Todokede, Todokede.CODE, Todokede.NAME, Todokede.CODE)
    todokede_list = get_notification_list()
    assert todokede_list[0] == ["", ""]
    assert todokede_list[1] == [1, "遅刻"]

@pytest.mark.skip
def test_toggle_notification_type(app_context):
    result = toggle_notification_type(Todokede, 3)
    print(result)
    assert result == "年休全日"

def test_convert_object_time(app_context):
    notification_obj = NotificationList.query.get(5)
    START_TIME: datetime = notification_obj.START_TIME
    END_TIME: datetime = notification_obj.END_TIME
    replaced_one_obj: NotificationList = convert_object_time(START_TIME, END_TIME)
    print(replaced_one_obj.START_TIME.strftime(''))
    print(replaced_one_obj.END_TIME.strftime(''))

