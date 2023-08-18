from datetime import datetime
from enum import IntEnum
from typing import List

from flask import render_template, redirect, request
from flask_login import current_user
from flask_login.utils import login_required
from flask.helpers import url_for

from app import app, db
from app.common_func import GetPullDownList
from app.models import (User, StaffLoggin, Todokede, SystemInfo)
from app.models_aprv import (NotificationList, Approval)
from app.errors import not_admin
from app.approval_util import (convert_str_to_date, convert_str_to_time,
                               toggle_notification_type)
from app.approval_contact import (ask_approval, send_mail)

"""
    戻り値に代入される変数名は、必ずstf_login！！
    """
# この関数注意！
# def appare_global_staff() -> StaffLoggin:
#     current_staff = StaffLoggin.query.get(current_user.STAFFID)
#     return current_staff

# フラグ関数、現urlを取得
# 2度使用するためこちら
def get_current_url_flag() -> bool:
    current_url = request.path
    flag = False
    flag = True if '/approval-list/charge' in current_url else flag
    return flag

# 申請リストページ    
@app.route('/notification-list/<STAFFID>', methods=['GET'])
@login_required
def get_notification_list(STAFFID):
    # notification_list = NotificationList.query.filter(NotificationList.STAFFID == STAFFID).all()

    user_basic_info: User = User.query.with_entities(User.STAFFID, User.LNAME, User.FNAME).filter(User.STAFFID==STAFFID).first()
    user_notification_list = NotificationList.query.with_entities(NotificationList.NOTICE_DAYTIME, Todokede.NAME,
                                               NotificationList.START_DAY, NotificationList.START_TIME,
                                               NotificationList.END_DAY, NotificationList.END_TIME,
                                               NotificationList.REMARK,
                                               NotificationList.id, NotificationList.STAFFID)\
                                                .filter(NotificationList.STAFFID==STAFFID)\
                                                    .join(Todokede, Todokede.CODE==NotificationList.N_CODE).all()
    
    return render_template('attendance/notification_list.html', 
                           uinfo=user_basic_info,
                           nlst=user_notification_list,
                           f=get_current_url_flag(),
                           stf_login=current_user
                           )

class StatusEnum(IntEnum):
    申請中 = 0
    承認済 = 1
    未承認 = 2

def auth_approval_user(func):
    def wrapper(*args, **kwargs):
        if current_user:
            approval_certificate_user = Approval.query.filter(Approval.STAFFID==current_user.STAFFID).first()
            if approval_certificate_user is None:
                return not_admin()
        # else:
        #     return redirect('/login')
            return func(approval_certificate_user)
        # return func(approval_certificate_user)
        return redirect(url_for('login'))
    return wrapper

# 承認待ちリストページ
@app.route('/approval-list/charge', methods=['GET'])
@login_required
# @auth_approval_user
# def get_middle_approval(approval_user):
def get_middle_approval():

    all_notification_list = (NotificationList.query.with_entities(NotificationList.NOTICE_DAYTIME, NotificationList.STAFFID,
                                               User.LNAME, User.FNAME, Todokede.NAME, NotificationList.STATUS,
                                               NotificationList.START_DAY, NotificationList.START_TIME,
                                               NotificationList.END_DAY, NotificationList.END_TIME,
                                               NotificationList.id)
                                                # .filter(NotificationList.STATUS==0)
                                                .join(User, User.STAFFID==NotificationList.STAFFID, isouter=True)
                                                .join(Todokede, Todokede.CODE==NotificationList.N_CODE)
                                                .all())

    return render_template('attendance/notification_list.html',
                           nlst=all_notification_list,
                           f=get_current_url_flag(),
                           s_enum=StatusEnum,
                           stf_login=current_user)

# 承認詳細ページ
@app.route('/confirm/<STAFFID>/<id>', methods=['GET'])
@login_required
def get_individual_approval(id: int, STAFFID=None):
    notification_row = NotificationList.query.get(id)

    data_list = []
    # 内容
    data_list.append(toggle_notification_type(Todokede, notification_row.N_CODE))
    # 対象日
    data_list.append(notification_row.START_DAY)
    # 対象終了日
    data_list.append(notification_row.END_DAY)
    # 開始時刻
    data_list.append(notification_row.START_TIME)
    # 終了時刻
    data_list.append(notification_row.END_TIME)
    # 備考
    data_list.append(notification_row.REMARK)
    # 承認状態
    data_list.append(StatusEnum(notification_row.STATUS).name)
    # そしてNotificationList.id
    data_list.append(notification_row.id)

    # フラグ関数、直前のurlを取得
    def get_url_past_flag() -> bool:
        past = request.referrer
        flag = False
        flag = True if 'charge' in past else flag
        return flag
    
    # 申請待ちユーザー
    approval_wait_user = User.query.get(STAFFID)

    return render_template('attendance/approval_confirm.html',
                           one_data=data_list,
                           f=get_url_past_flag(),
                           w_usr=approval_wait_user,
                           stf_login=current_user)

# 届出内容対照を返す関数
def get_notification_list():
    todokede_list = GetPullDownList(Todokede, Todokede.CODE, Todokede.NAME,
                                  Todokede.CODE)
    return todokede_list

# 申請入力フォームページ
@app.route('/approval-form', methods=['GET', 'POST'])
@login_required
def get_notification_form():
    # if request.method == 'GET':
        notification_all = get_notification_list()

        user_detail = User.query.get(current_user.STAFFID)

        return render_template('attendance/approval_form.html', 
                            n_all=notification_all,
                            stf_login=user_detail
                            )
    
    # elif request.method == 'POST':

"""
    request.form(input name)から値を取り出しlistに追加
    Param:
        form_data: List[str]
    Return:
        list_data: list
    """
def retrieve_form_data(form_data: List[str]) -> list:
    list_data = []
    for fdata in form_data:
        list_data.append(request.form.get(fdata))
    
    return list_data

# 申請確認ページ
@app.route('/confirm', methods=['POST'])
@login_required
def post_approval():
    # 取り出したいformの項目
    approval_list = ['start-day', 'end-day', 'start-time', 'end-time', 'remark']
    form_list_data = retrieve_form_data(approval_list)

    # 数値(CODE)を文字列(NAME)に入れ替え
    form_content: str = toggle_notification_type(Todokede, int(request.form.get('content')))
    # 先頭に挿入
    form_list_data.insert(0, form_content)

    return render_template('attendance/approval_confirm.html', 
                        one_data=form_list_data,
                        stf_login=current_user)

# DBinsert & skype送信ページ
@app.route('/regist', methods=['POST'])
@login_required
def append_approval():

    # こちらは数値(CODE)に変換
    form_content: int = toggle_notification_type(Todokede, request.form.get('content'))
    
    form_start_day: datetime = convert_str_to_date(request.form.get('start-day'))
    form_end_day: datetime = convert_str_to_date(request.form.get('end-day'))
    form_start_time: datetime = convert_str_to_time(request.form.get('start-time'))
    form_end_time: datetime = convert_str_to_time(request.form.get('end-time'))
    form_remark: str = request.form.get('remark')

    one_notification = NotificationList(
        current_user.STAFFID, form_content, form_start_day, form_start_time,
        form_end_day, form_end_time, form_remark
    )

    db.session.add(one_notification)
    db.session.commit()

    # skypeにて、申請の通知
    asking_user = User.query.get(current_user.STAFFID)
    asking_message = f"「{asking_user.LNAME} {asking_user.FNAME}」さんから申請依頼が来ています。\n\
        {request.url_root}approval-list/charge"
    
    ask_approval(asking_message)

    return redirect('/')

"""
    申請依頼に対して、許可か拒否か、DBupdate
    Param:
        id: int
        judgement: int
    Return:
        : None
    """
def change_status(id: int, judgement: int) -> None:
    detail_notification: NotificationList = NotificationList.query.get(id)
    detail_notification.STATUS = judgement

    db.session.merge(detail_notification)
    db.session.commit()

# 申請に対して、承認
@app.route('/approval_ok/<STAFFID>/<id>', methods=['POST'])
@login_required
def change_status_ok(id, STAFFID):
    change_status(id, 1)

    approval_wait_user = SystemInfo.query.filter(SystemInfo.STAFFID==STAFFID).first()
    
    approval_reply_user = SystemInfo.query.filter(SystemInfo.STAFFID==current_user.STAFFID).first()

    target_notification = NotificationList.query.get(id)

    approval_reply_message = \
        f"{target_notification.START_DAY}:\
            {toggle_notification_type(Todokede, target_notification.N_CODE)}\
                \n{target_notification.REMARK}\
                \n\n{request.form.get('comment')}"

    # 承認者よりコメントをメールで
    send_mail(approval_reply_user.MAIL, approval_wait_user.MAIL,
              approval_reply_user.MAIL_PASS, approval_reply_message)

    # return redirect(url_for('get_individual_approval', id=id, STAFFID=current_user.STAFFID))
    return redirect(url_for('get_middle_approval'))

# 申請に対して、拒否
@app.route('/approval_ng/<STAFFID>/<id>', methods=['POST'])
@login_required
def change_status_ng(id, STAFFID):
    change_status(id, 2)

    approval_wait_user = SystemInfo.query.filter(SystemInfo.STAFFID==STAFFID).first()
    # approval_reply_user_mail: str = (Approval.query.with_entities(SystemInfo.MAIL)
    #                        .filter(Approval.STAFFID==current_user.STAFFID)
    #                        .join(SystemInfo, SystemInfo.STAFFID==Approval.STAFFID, isouter=True)
    #                        .first())
    approval_reply_user = SystemInfo.query.filter(SystemInfo.STAFFID==current_user.STAFFID).first()
    
    send_mail(approval_reply_user.MAIL, approval_wait_user.MAIL,
              approval_reply_user.MAIL_PASS, request.form.get('comment'))

    # return redirect(url_for('get_individual_approval', id=id, STAFFID=current_user.STAFFID))
    return redirect(url_for('get_middle_approval'))
