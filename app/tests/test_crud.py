import pytest
import datetime
import json
from bson.json_util import dumps

from app.models_aprv import (NotificationList, Approval)
from app.models import (User, SystemInfo)
from app.models_tt import (TodoOrm, TodoModel)

# sample_end_datetime = datetime(2023, 9, 30, 1, 1, 59)

@pytest.mark.skip
def test_sample_add_notification_data(app_context):
    notification_1 = NotificationList(30, 8,
                                      datetime.datetime.now().date(), datetime.datetime.now().time(),
                                      datetime.datetime.now().date() + datetime.timedelta(days=3),
                                      datetime.datetime.now().time(), "軒下の雪で")
    db.session.add(notification_1)
    db.session.commit()

@pytest.mark.skip
def test_select_notification_data(app_context):
    one_notification_data = NotificationList.query.filter(NotificationList.STAFFID==20).all()
    assert len(one_notification_data) == 2

@pytest.mark.skip
def test_get_staff_data(app_context):
    # 所属コード
    team_code = User.query.with_entities(User.TEAM_CODE)\
        .filter(User.STAFFID==201).first()
    
    approval_member: Approval = Approval.query.filter(Approval.TEAM_CODE==team_code[0]).first()
    # 承認者Skypeログイン情報
    skype_account = SystemInfo.query.with_entities(SystemInfo.MAIL, SystemInfo.MAIL_PASS)\
        .filter(SystemInfo.STAFFID==approval_member.STAFFID).first()
    
    assert skype_account.MAIL == "win_mint.7v903@outlook.jp"
    assert type(approval_member) == Approval
    # assert team_code == 2

td_orm = TodoOrm(summary="test summary", owner="YuenBiao")
def test_print_todo_data(app_context):
    # td_model = TodoModel.model_validate(td_orm)
    todos = TodoOrm.query.all()
    print(json.loads(dumps([str(todo) for todo in todos])))
    # db.session.add(td_model)
    # db.session.commit()

