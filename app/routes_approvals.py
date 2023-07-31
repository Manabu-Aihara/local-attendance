from datetime import datetime

from flask import render_template, redirect, request
from flask_login import current_user
from flask_login.utils import login_required
from flask.helpers import url_for

from app import app, db
from app.common_func import GetPullDownList
from app.models import StaffLoggin, Todokede
from app.models_aprv import NotificationList

"""
    結局使わないデコレータ
    """
# def stuff_login_require(num):
def stuff_login_require(func):
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        else:
            effective_user = StaffLoggin.query.get(current_user.STAFFID)
        return func(effective_user)
    return wrapper
    # return _stuff_login_require

"""
    戻り値に代入される変数は、必ずstf_login！！
    """
def appare_global_staff() -> StaffLoggin:
    current_staff = StaffLoggin.query.get(current_user.STAFFID)
    return current_staff

@app.route('/approval-list/<STAFFID>', methods=['GET'])
@login_required
def get_approval_list(STAFFID):
    notification_list = NotificationList.query.filter(NotificationList.STAFFID == STAFFID).all()
    return render_template('attendance/notification_list.html', 
                           nlst=notification_list,
                           stf_login=appare_global_staff()
                           )
"""
    申請理由プルダウンリスト
    @Param
    Table object
    Table code
    Table name
    sort基準
    """
def get_notification_list():
    todokede_list = GetPullDownList(Todokede, Todokede.CODE, Todokede.NAME,
                                  Todokede.CODE)
    return todokede_list

def retrieve_form_data(list_data: list) -> list:
    form_data = []
    for ldata in list_data:
        form_data.append(request.form.get(ldata))
    
    return form_data

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

@app.route('/confirm', methods=['POST'])
@login_required
def post_approval():
    approval_list = ['content', 'start-day', 'end-day', 'start-time', 'end-time', 'remark']
    form_list_data = retrieve_form_data(approval_list)

    return render_template('attendance/approval_confirm.html', 
                        one_data=form_list_data,
                        stf_login=appare_global_staff())


def convert_str_to_date(arg) -> datetime | None:
    if arg != None:
        conv_date = datetime.strptime(arg, '%Y-%m-%d')
        return conv_date
    else:
        return None

def convert_str_to_time(arg) -> datetime | str:
    if arg != None:
        conv_time = datetime.strptime(arg, '%H:%M')
        return conv_time
    else:
        return '%H:%M'

@app.route('/regist', methods=['POST'])
@login_required
def append_approval():
    form_content = request.form.get('content')
    form_start_day = convert_str_to_date(request.form.get('start-day'))
    form_end_day: datetime | None = convert_str_to_date(request.form.get('end-day'))
    form_start_time: datetime | str = convert_str_to_time(request.form.get('start-time'))
    form_end_time: datetime | str = convert_str_to_time(request.form.get('end-time'))
    form_remark = request.form.get('remark')

    one_notification = NotificationList(
        current_user.STAFFID, form_content, form_start_day, form_start_time,
        form_end_day, form_end_time, form_remark
    )

    db.session.add(one_notification)
    db.session.commit()

    return redirect('/')
