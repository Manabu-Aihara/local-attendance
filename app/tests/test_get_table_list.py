from app.common_func import GetPullDownList
from app.models import Todokede
from app.routes_approvals import get_notification_list

def test_get_notificatin_list(app_context):
    # todokede_list = GetPullDownList(Todokede, Todokede.CODE)
    todokede_list = get_notification_list()
    assert todokede_list[0] == ["", ""]
    assert todokede_list[1] == [1, "遅刻"]
