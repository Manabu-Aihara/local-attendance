from flask import render_template, redirect, request
from flask_login import current_user
from flask_login.utils import login_required
from flask.helpers import url_for

from app import app
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
def appare_global_staff():
    current_staff = StaffLoggin.query.get(current_user.STAFFID)
    return current_staff

@app.route('/approval-list/<STAFFID>', methods=['GET'])
@login_required
def get_approval_list(STAFFID):
    notification_list = NotificationList.query.get(STAFFID)
    return render_template('attendance/notification_list.html', 
                           nlst=notification_list,
                           stf_login=appare_global_staff()
                           )

def get_notification_list():
    todokede_list = GetPullDownList(Todokede, Todokede.CODE, Todokede.NAME,
                                  Todokede.CODE)
    return todokede_list

@app.route('/approval-form')
@login_required
def get_notification_form():
    notification_all = get_notification_list()
    return render_template('attendance/approval_form.html', 
                        stf_login=appare_global_staff(),
                        n_all=notification_all
                        )


@app.route('/approval-form', methods=['POST'])
@login_required
def post_approval():
    form_reason = request.form.get('notice')
    form_start_day = request.form.get('start-day')
    form_end_day = request.form.get('end-day')
    form_start_time = request.form.get('start-time')
    form_end_time = request.form.get('end-day')
    form_remark = request.form.get('remark')

    one_notification = NotificationList(
        current_user.STAFFID, form_reason, 0, form_start_day, form_start_time,
        form_end_day, form_end_time, form_remark
    )

    return redirect(url_for('get_confirm', value=one_notification))

@app.route('/confirm', methods=['GET', 'POST'])
@login_required
def get_confirm(value: NotificationList):
    return render_template('attendance/approval_confirm.html', 
                           one_data=value,
                           stf_login=appare_global_staff())
