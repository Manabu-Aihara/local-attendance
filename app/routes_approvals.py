from datetime import datetime, time

from flask import render_template, redirect, request
from flask_login import current_user
from flask_login.utils import login_required
from flask.helpers import url_for

from app import app, db
from app.common_func import GetPullDownList
from app.models import StaffLoggin, Todokede
from app.models_aprv import NotificationList
from app.approval_util import (convert_str_to_date, convert_str_to_time,
                               toggle_notification_type, replace_uneffective_index_time)

"""
    戻り値に代入される変数名は、必ずstf_login！！
    """
def appare_global_staff() -> StaffLoggin:
    current_staff = StaffLoggin.query.get(current_user.STAFFID)
    return current_staff

@app.route('/approval-list/<STAFFID>', methods=['GET'])
@login_required
def get_approval_list(STAFFID):
    notification_list = NotificationList.query.filter(NotificationList.STAFFID == STAFFID).all()

    # for nlst in notification_list:
    #     nlst.START_TIME.strftime('%H:%M').replace("00:00:00", "")
    #     nlst.END_TIME.strftime('%H:%M').replace("00:00:00", "")
    # out_index = search_uneffective_time_index(notification_list)
    # for oi in out_index:
    #     notification_list[oi].START_TIME.strftime('%H:%M:%S').replace("00:00:00", "")
    #     notification_list[oi].END_TIME.strftime('%H:%M:%S').replace("00:00:00", "")
    # type_list_time = replace_uneffective_index_time(notification_list)
    # for lt in type_list_time:
    #     return lt
    
    # return notification_list[3].START_TIME.strftime('%H:%M:%S')
    return render_template('attendance/notification_list.html', 
                           nlst=notification_list,
                           stf_login=appare_global_staff()
                           )

@app.route('/confirm/<STAFFID>/<id>', methods=['GET'])
@login_required
def get_individual_approval(STAFFID, id: int):
    notification_row = NotificationList.query.get(id)

    table_columns = []
    # https://teratail.com/questions/214028
    table_columns.append(NotificationList.__table__.c.keys()[2:])

    date_list = []
    date_list.append(NotificationList.query.filter(notification_row.N_CODE==table_columns[0])).first()
    
    # return render_template('attendance/approval_confirm.html',
    #                        one_data=notification_row,
    #                        stf_login=appare_global_staff())

def get_notification_list():
    todokede_list = GetPullDownList(Todokede, Todokede.CODE, Todokede.NAME,
                                  Todokede.CODE)
    return todokede_list

@app.route('/approval-form', methods=['GET', 'POST'])
@login_required
def get_notification_form():
    # if request.method == 'GET':
        notification_all = get_notification_list()
        return render_template('attendance/approval_form.html', 
                            stf_login=appare_global_staff(),
                            n_all=notification_all
                            )
    
    # elif request.method == 'POST':

def retrieve_form_data(list_data: list[str]) -> list:
    form_data = []
    for ldata in list_data:
        form_data.append(request.form.get(ldata))
    
    return form_data

@app.route('/confirm', methods=['POST'])
@login_required
def post_approval():
    approval_list = ['start-day', 'end-day', 'start-time', 'end-time', 'remark']
    form_list_data = retrieve_form_data(approval_list)
    # 数値(CODE)を文字列(NAME)に入れ替え
    form_content: str = toggle_notification_type(Todokede, int(request.form.get('content')))
    form_list_data.insert(0, form_content)

    return render_template('attendance/approval_confirm.html', 
                        one_data=form_list_data,
                        stf_login=appare_global_staff())

@app.route('/regist', methods=['POST'])
@login_required
def append_approval():
    # out_apprpval_valid = OutputApprovalDataConversion()

    # こちらは数値(CODE)に変換
    form_content: int = toggle_notification_type(Todokede, request.form.get('content'))
    form_start_day: datetime = convert_str_to_date(request.form.get('start-day'))
    form_end_day: datetime = convert_str_to_date(request.form.get('end-day'))
    form_start_time: datetime = convert_str_to_time(request.form.get('start-time'))
    form_end_time: datetime = convert_str_to_time(request.form.get('end-time'))
    form_remark = request.form.get('remark')

    one_notification = NotificationList(
        current_user.STAFFID, form_content, form_start_day, form_start_time,
        form_end_day, form_end_time, form_remark
    )

    db.session.add(one_notification)
    db.session.commit()

    return redirect('/')
