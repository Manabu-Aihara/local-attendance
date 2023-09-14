"""
**********
勤怠システム
2022/04版
**********
"""
# from app import routes_admin_nenkyu, routes_admin_display_table
from flask import render_template, flash, redirect, request, session
from werkzeug.urls import url_parse
from flask.helpers import url_for
from flask_login.utils import login_required
from app import app, db
from app.forms import LoginForm, AdminUserCreateForm, ResetPasswordForm, DelForm, UpdateForm, SaveForm, EditForm, AddDataUserForm, SelectMonthForm
# from app.user_add_forms import LoginForm, AdminUserCreateForm, ResetPasswordForm, DelForm, UpdateForm, SaveForm, EditForm, AddDataUserForm, SelectMonthForm
from flask_login import current_user, login_user
from app.models import User, Shinsei, StaffLoggin, Todokede, RecordPaidHoliday, CountAttendance, TimeAttendance, SystemInfo, CounterForTable
from flask_login import logout_user
from flask import abort
from functools import wraps
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta, date
from decimal import Decimal, ROUND_HALF_UP
import jpholiday
import os
from dateutil.relativedelta import relativedelta
from monthdelta import monthmod
from app.attendance_admin_classes import AttendanceAdminAnalysys
from app.calender_classes import MakeCalender
from app.calc_work_classes import DataForTable, CalcTimeClass, PartCalcHolidayTimeClass


os.environ.get('SECRET_KEY') or 'you-will-never-guess'
app.permanent_session_lifetime = timedelta(minutes=360)


"""***** 管理者か判断 *****"""

def admin_login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_admin():
            return abort(403)
        return func(*args, **kwargs)
    return decorated_view


"""***** 管理者関連 *****"""


@app.route('/admin')
@login_required
@admin_login_required
def home_admin():
    return render_template('admin/admin-home.html')


#***** ユーザリストページ *****#
@app.route('/admin/users-list')
@login_required
@admin_login_required
def users_list_admin():
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    users = StaffLoggin.query.all()
    us = User.query.all()
    
    return render_template('admin/users-list-admin.html', users=users, us=us, stf_login=stf_login)


#***** ユーザ登録ページ *****#
@app.route('/admin/create-user', methods=['GET', 'POST'])
@login_required
@admin_login_required
def user_create_admin():
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    mes = None
    form = AdminUserCreateForm()
    if form.validate_on_submit():
        STAFFID = form.staffid.data
        PASSWORD = form.password.data
        ADMIN = form.admin.data
        existing_username = StaffLoggin.query.filter_by(
            STAFFID=STAFFID).first()
        if existing_username:
            mes = "この社員番号は既に存在します。"
            flash('この社員番号は既に存在します。', 'warning')

            return render_template('admin/user-create-admin.html', form=form, mes=mes, stf_login=current_user)        
        stl = StaffLoggin(STAFFID, PASSWORD, ADMIN)
        usr = User(STAFFID)
        rp_holiday = RecordPaidHoliday(STAFFID=STAFFID)
        sys_info = SystemInfo(STAFFID=STAFFID)
        cnt_attendance = CountAttendance(STAFFID=STAFFID)
        tm_attendance = TimeAttendance(STAFFID=STAFFID)
        cnt_for_tbl = CounterForTable(STAFFID=STAFFID)
        
        db.session.add(rp_holiday)
        db.session.add(cnt_attendance)
        db.session.add(tm_attendance)
        db.session.add(cnt_for_tbl)
        db.session.add(sys_info)
        db.session.add(stl)
        db.session.add(usr)
        db.session.commit()
        flash('続いて、追加のユーザデータを作成します', 'info')

        return redirect(url_for('edit_data_user', STAFFID=STAFFID, intFlg=0))

    if form.errors:
        flash(form.errors, 'danger')

    return render_template('admin/user-create-admin.html', form=form, mes=mes, stf_login=stf_login)





#***** ユーザ編集（リスト）ページ *****#
@app.route('/admin/edit_list_user', methods=['GET', 'POST'])
@login_required
@admin_login_required
def edit_list_user():
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    usr = User.query.all()
    department = ["本社", "宇介", "下介", "鹿介", "KO介", "宇福", "KO福", "鹿福", "筑波介"]
    team = ["本社", "宇都宮", "下野", "鹿沼", "KODOMOTO", "在宅支援", "KOそうだん", "つくば"]
    contract = ["８H常勤", "パート", "６H常勤", "７H常勤", "３２H常勤"]
    jobtype = ["NS", "事務", "OT", "ST", "PT", "相談支援", "相談補助", "保育支援", "准NS", "開発", "広報"]
    post = ["所長", "副所長", "主任", "スタッフリーダー"]
    
    if request.method == 'POST':
        return redirect(url_for('edit_data_user', STAFFID=STAFFID))
    
    return render_template('admin/edit_list_user.html', usr=usr, department=department, team=team, contract=contract, jobtype=jobtype,
                           post=post, stf_login=stf_login, intFlg=1)


#***** ユーザ編集ページ *****#
@app.route('/admin/edit_data_user/<STAFFID>/<int:intFlg>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def edit_data_user(STAFFID, intFlg):
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    form = AddDataUserForm()
    STAFFID=STAFFID
    u = User.query.get(STAFFID)
    rp_holiday = RecordPaidHoliday.query.get(STAFFID)
    cnt_attendance = CountAttendance.query.get(STAFFID)
    tm_attendance = TimeAttendance.query.get(STAFFID)
    cnt_for_tbl = CounterForTable.query.get(STAFFID)
    sys_info = SystemInfo.query.get(STAFFID)

    if form.validate_on_submit():
        if form.department.data == 0:
            DEPARTMENT_CODE = 0
        else:
            DEPARTMENT_CODE = form.department.data
            
        if form.team.data == 0:
            TEAM_CODE = 0
        else:
            TEAM_CODE = form.team.data

        if form.contract.data == 0:
            CONTRACT_CODE = 0
        else:
            CONTRACT_CODE = form.contract.data

        if form.jobtype.data == 0:
            JOBTYPE_CODE = 0
        else:
            JOBTYPE_CODE = form.jobtype.data

        if form.post_code.data == 0:
            POST_CODE = 0
        else:
            POST_CODE = form.post_code.data
            
        if form.worker_time.data == "" or form.worker_time.data == None:
            WORKER_TIME = int("0")
        else:
            WORKER_TIME = int(form.worker_time.data)

        if form.basetime_paidholiday.data == "" or form.basetime_paidholiday.data == None:
            BASETIMES_PAIDHOLIDAY = float("0")
        else:
            BASETIMES_PAIDHOLIDAY = float(form.basetime_paidholiday.data)
            
        if form.last_carriedover.data == "" or form.last_carriedover.data == None:
            LAST_CARRIEDOVER = float("0")
        else:
            LAST_CARRIEDOVER = float(form.last_carriedover.data)
            
        if form.social.data == 0:
            SOCIAL_INSURANCE = 0
        else:
            SOCIAL_INSURANCE = form.social.data
            
        if form.employee.data == 0:
            EMPLOYMENT_INSURANCE = 0
        else:
            EMPLOYMENT_INSURANCE = form.employee.data
        EXPERIENCE = form.experi.data
        TABLET = form.tablet.data
        SINGLE = form.single.data
        SUPPORT = form.support.data
        HOUSE = form.house.data
        DISTANCE = form.distance.data
        LNAME = form.lname.data
        FNAME = form.fname.data
        LKANA = form.lkana.data
        FKANA = form.fkana.data
        POST = form.post.data
        ADRESS1 = form.adress1.data
        ADRESS2 = form.adress2.data
        TEL1 = form.tel1.data
        TEL2 = form.tel2.data
        BIRTHDAY = form.birthday.data
        INDAY = form.inday.data

        OUTDAY = form.outday.data
        STANDDAY = form.standday.data

        WORKER_TIME = form.worker_time.data
        BASETIMES_PAIDHOLIDAY = form.basetime_paidholiday.data 

        REMARK = form.remark.data
        MAIL = form.m_a.data
        MAIL_PASS = form.ml_p.data
        MICRO_PASS = form.ms_p.data
        PAY_PASS = form.p_p.data
        KANAMIC_PASS = form.k_p.data
        ZOOM_PASS = form.z_p.data

        u.DEPARTMENT_CODE=DEPARTMENT_CODE
        u.TEAM_CODE=TEAM_CODE 
        u.CONTRACT_CODE=CONTRACT_CODE
        u.JOBTYPE_CODE=JOBTYPE_CODE
        u.POST_CODE=POST_CODE
        u.LNAME=LNAME
        u.FNAME=FNAME
        u.LKANA=LKANA
        u.FKANA=FKANA
        u.POST=POST
        u.ADRESS1=ADRESS1 
        u.ADRESS2=ADRESS2
        u.TEL1=TEL1
        u.TEL2=TEL2
        u.BIRTHDAY=BIRTHDAY
        u.INDAY=INDAY
        u.OUTDAY=OUTDAY
        u.STANDDAY=STANDDAY
        u.SOCIAL_INSURANCE=SOCIAL_INSURANCE
        u.EMPLOYMENT_INSURANCE=EMPLOYMENT_INSURANCE
        u.EMPLOYMENT_INSURANCE=EMPLOYMENT_INSURANCE
        u.EXPERIENCE=EXPERIENCE
        u.TABLET=TABLET
        u.SINGLE=SINGLE
        u.SUPPORT=SUPPORT
        u.HOUSE=HOUSE
        u.DISTANCE=DISTANCE
        u.REMARK=REMARK
        db.session.commit()
        
        rp_holiday.DEPARTMENT_CODE=DEPARTMENT_CODE
        rp_holiday.LNAME=LNAME
        rp_holiday.FNAME=FNAME
        rp_holiday.LKANA=LKANA
        rp_holiday.FKANA=FKANA
        rp_holiday.INDAY=INDAY
        # OUTDAYはM_RemainPaidHolidayにはない
        rp_holiday.TEAM_CODE=TEAM_CODE
        rp_holiday.CONTRACT_CODE=CONTRACT_CODE
        rp_holiday.DUMP_REFLESH=0
        rp_holiday.DUMP_REFLESH_CHECK=0
                 
        rp_holiday.WORK_TIME = WORKER_TIME
        rp_holiday.BASETIMES_PAIDHOLIDAY = BASETIMES_PAIDHOLIDAY
        rp_holiday.LAST_CARRIEDOVER = LAST_CARRIEDOVER
        
        db.session.commit()
    
        sys_info.MAIL = MAIL
        sys_info.MAIL_PASS = MAIL_PASS
        sys_info.MICRO_PASS = MICRO_PASS
        sys_info.PAY_PASS = PAY_PASS
        sys_info.KANAMIC_PASS = KANAMIC_PASS
        sys_info.ZOOM_PASS = ZOOM_PASS
        db.session.commit()

    
        flash('ユーザ情報を編集しました', 'info')
        return redirect(url_for('edit_list_user'))
    
    elif intFlg == 1:
        
        form.department.data = u.DEPARTMENT_CODE
        form.team.data = u.TEAM_CODE
        form.contract.data = u.CONTRACT_CODE
        form.jobtype.data = u.JOBTYPE_CODE
        form.post_code.data = u.POST_CODE
        form.lname.data = u.LNAME
        form.fname.data = u.FNAME
        form.lkana.data = u.LKANA
        form.fkana.data = u.FKANA
        form.post.data = u.POST
        form.adress1.data = u.ADRESS1
        form.adress2.data = u.ADRESS2
        form.tel1.data = u.TEL1
        form.tel2.data = u.TEL2
        form.birthday.data = u.BIRTHDAY
        form.inday.data = u.INDAY
        form.outday.data = u.OUTDAY
        form.standday.data = u.STANDDAY
        form.remark.data = u.REMARK
        form.m_a.data = sys_info.MAIL
        form.ml_p.data = sys_info.MAIL_PASS
        form.ms_p.data = sys_info.MICRO_PASS
        form.p_p.data = sys_info.PAY_PASS
        form.k_p.data = sys_info.KANAMIC_PASS
        form.z_p.data = sys_info.ZOOM_PASS
        form.worker_time.data = rp_holiday.WORK_TIME
        form.basetime_paidholiday.data = rp_holiday.BASETIMES_PAIDHOLIDAY
        form.last_carriedover.data = rp_holiday.LAST_CARRIEDOVER 
        
        if u.SOCIAL_INSURANCE == 0:
            form.social.data = 0
        else:
            form.social.data = 1
            
        if u.EMPLOYMENT_INSURANCE == 0:
            form.employee.data = 0
        else:
            form.employee.data = 1
        
        if u.EXPERIENCE == 0 or u.EXPERIENCE is None:
            form.experi.data = 0
        else:
            form.experi.data = u.EXPERIENCE

        if u.TABLET == 0 or u.TABLET is None:
            form.tablet.data = 0
        else:
            form.tablet.data = u.TABLET
        
        if u.SINGLE == 0 or u.SINGLE is None:
            form.single.data = 0
        else:
            form.single.data = u.SINGLE
        
        if u.SUPPORT == 0 or u.SUPPORT is None:
            form.support.data = 0
        else:
            form.support.data = u.SUPPORT

        if u.HOUSE == 0 or u.HOUSE is None:
            form.house.data = 0
        else:
            form.house.data = u.HOUSE
        
        form.distance.data = u.DISTANCE


        
            

    if form.errors:
        flash(form.errors, 'danger')

    return render_template('admin/edit_data_user.html', form=form, STAFFID=STAFFID, u=u, stf_login=stf_login, intFlg=intFlg)


@app.route('/admin/delete-user/<STAFFID>')
@login_required
@admin_login_required
def user_delete_admin(STAFFID):
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    shinseis = Shinsei.query.filter_by(STAFFID=STAFFID).all()    
    stls = StaffLoggin.query.filter_by(STAFFID=STAFFID).all()
    rp_holiday = RecordPaidHoliday.query.get(STAFFID)
    usrs = User.query.get(STAFFID)
    cnt_attendance = CountAttendance.query.get(STAFFID)
    tm_attendance = TimeAttendance.query.get(STAFFID)
    cnt_for_tbl = CounterForTable.query.get(STAFFID)
    sys_info = SystemInfo.query.get(STAFFID)
    
    if shinseis:
        for sh in shinseis:
            db.session.delete(sh)
            db.session.commit()
    
    if stls:    
        for st in stls:
            db.session.delete(st)
            db.session.commit()

    if rp_holiday:      
        db.session.delete(rp_holiday)
        db.session.commit()
        
    if sys_info:        
        db.session.delete(sys_info)
        db.session.commit()      
    
    if cnt_attendance:        
        db.session.delete(cnt_attendance)
        db.session.commit()
        
    if tm_attendance:       
        db.session.delete(tm_attendance)
        db.session.commit() 
    
    if cnt_for_tbl:       
        db.session.delete(cnt_for_tbl)
        db.session.commit()                 

    if usrs:
        db.session.delete(usrs)
        db.session.commit()

    flash('ユーザを削除しました', 'info')
    return redirect(url_for('home_admin'))


#***** ユーザパスワードリセット *****#
@app.route('/admin/reset_password/<STAFFID>', methods=['GET', 'POST'])
@login_required
@admin_login_required
def reset_token(STAFFID):
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    STAFFID = STAFFID
    shinseis = Shinsei.query.filter_by(STAFFID=STAFFID).all()
    u = User.query.get(STAFFID)
    
    hid_a = ""
    hid_b = "hidden"
    form = ResetPasswordForm()
    if form.validate_on_submit():
        STAFFID = STAFFID
        
        if form.PASSWORD.data != form.PASSWORD2.data:
            hid_a = "hidden"
            hid_b = ""
            return render_template('attendance/reset_token.html', title='Reset Password', form=form, STAFFID=STAFFID,
                                   shinseis=shinseis, u=u, hid_a=hid_a, hid_b=hid_b)
        elif form.PASSWORD.data == form.PASSWORD2.data: 
            HASHED_PASSWORD = generate_password_hash(form.PASSWORD.data)
            ADMIN = form.ADMIN.data

            StaffLoggin.query.filter_by(STAFFID=STAFFID).update(
                dict(PASSWORD_HASH=HASHED_PASSWORD, ADMIN=ADMIN))
            db.session.commit()
            
            return redirect(url_for('indextime', STAFFID=STAFFID))

    if form.errors:
        flash("エラーが発生しました。")

    return render_template('admin/reset_token.html', title='Reset Password', form=form, STAFFID=STAFFID, shinseis=shinseis, 
                           u=u, hid_a=hid_a, hid_b=hid_b, stf_login=stf_login)


@ app.route('/admin/users_detail/<STAFFID>', methods=['GET', 'POST'])
@ login_required
@ admin_login_required
def users_detail(STAFFID):
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    STAFFID = STAFFID
    shinseis = Shinsei.query.filter_by(STAFFID=STAFFID).all()
    u = User.query.get(STAFFID)
    shin = Shinsei.query.filter_by(STAFFID=STAFFID)
    rp_holiday = RecordPaidHoliday.query.get(STAFFID)
    cnt_attemdance = CountAttendance.query.get(STAFFID)
    tm_attendance = TimeAttendance.query.get(STAFFID)

    ##### 表示関連 #####
    form_month = SelectMonthForm()

    tbl_clm = ["日付", "曜日", "oncall", "oncall対応件数", "angel対応件数",
               "開始時間", "終了時間", "走行距離", "届出（午前）", "残業申請", "備考", "届出（午後）"]
    wk = ["日", "土", "月", "火", "水", "木", "金"]
    ptn = ["^[0-9０-９]+$", "^[0-9.０-９．]+$"]
    specification = ["readonly", "checked", "selected", "hidden", "disabled"]
    typ = ["submit", "text", "time", "checkbox", "number", "month"]
    team_name = ["本社", "WADEWADE訪問看護ステーション宇都宮", "WADEWADE訪問看護ステーション下野", "WADEWADE訪問看護ステーション鹿沼",
                 "KODOMOTOナースステーションうつのみや", "わでわで在宅支援センターうつのみや", "わでわで子どもそうだんしえん",
                 "WADEWADE訪問看護ステーションつくば"]

    ##### カレンダーとM_NOTIFICATION土日出勤の紐づけ関数 #####

    def get_day_of_week_jp(dt):
        w_list = ['', '', '', '', '', '1', '1']
        return(w_list[dt.weekday()])

    ##### 社員職種・勤務形態によるページ振り分け #####
    if STAFFID == 10000:
        oc = "hidden"
        oc_cnt = "hidden"
        eg = "hidden"
        sk = "hidden"
        bk = "hidden"
        othr = "hidden"
    elif u.CONTRACT_CODE != 2 and u.JOBTYPE_CODE == 1:
        oc = ""
        oc_cnt = ""
        eg = ""
        sk = "hidden"
        bk = ""
        othr = ""
        
    elif u.CONTRACT_CODE != 2 and (u.JOBTYPE_CODE == 3 or u.JOBTYPE_CODE == 4 or u.JOBTYPE_CODE == 5 or \
        u.JOBTYPE_CODE == 6 or u.JOBTYPE_CODE == 7 or u.JOBTYPE_CODE == 8):
        oc = "hidden"
        oc_cnt = "hidden"
        eg = "hidden"
        sk = "hidden"
        othr = ""
        bk = "" 

    else:
        oc = "hidden"
        oc_cnt = "hidden"
        eg = "hidden"
        sk = ""
        othr = ""
        bk = ""
        
    ##### M_NOTIFICATIONとタイムカードの紐づけ #####
    td1 = Todokede.query.get(1)
    td2 = Todokede.query.get(2)
    td3 = Todokede.query.get(3)  # 年休（全日）はNotification2にはない
    td4 = Todokede.query.get(4)
    td5 = Todokede.query.get(5)  # 出張（全日）はNotification2にはない
    td6 = Todokede.query.get(6)
    td7 = Todokede.query.get(7)  # リフレッシュ休暇はNotification2にはない
    td8 = Todokede.query.get(8)  # 欠勤はNotification2にはない
    td9 = Todokede.query.get(9)
    td10 = Todokede.query.get(10)
    td11 = Todokede.query.get(11)
    td12 = Todokede.query.get(12)
    td13 = Todokede.query.get(13)
    td14 = Todokede.query.get(14)
    td15 = Todokede.query.get(15)
    td16 = Todokede.query.get(16)    
    td17 = Todokede.query.get(17)
    td18 = Todokede.query.get(18)
    td19 = Todokede.query.get(19)
    td20 = Todokede.query.get(20)


    ##### 月選択の有無 #####
    if "y" in session:
        workday_data = session["workday_data"]
        y = session["y"]
        m = session["m"]
    else:
        workday_data = datetime.today().strftime('%Y-%m-%d')
        y = datetime.now().year
        m = datetime.now().month

    ##### カレンダーの設定 #####
    
    cal = []
    hld = []
    
    mkc = MakeCalender(cal, hld, y, m)
    mkc.mkcal()
    
    ##### 年休登録 #####
    if shinseis is None:
        pass
    else:
        if User.query.get(STAFFID) is None:
            pass
        else:
            usr = User.query.get(STAFFID)
            rp_holiday = RecordPaidHoliday.query.get(STAFFID)

            inday = usr.INDAY
            team_code = usr.TEAM_CODE
            lname = usr.LNAME
            fname = usr.FNAME
            lkana = usr.LKANA
            fkana = usr.FKANA
            contract_code = usr.CONTRACT_CODE

            if inday is not None:
                ########## 本日計算ベース #########
                ##### 基準月に変換 #####
                if inday.month >= 4 and inday.month < 10:
                    change_day = inday.replace(month=10, day=1)  # 基準月
                    giveday = change_day  # 初回付与日
                elif inday.month >= 10 and inday.month <= 12:
                    change_day = inday.replace(month=4, day=1)  # 基準月
                    giveday = change_day + relativedelta(months=12)  # 初回付与日
                elif inday.month < 4:
                    change_day = inday.replace(month=4, day=1)  # 基準月
                    giveday = change_day  # 初回付与日

                ##### 基準付与日設定 #####
                # 新入職員
                if datetime.today() < giveday and monthmod(datetime.today(), giveday)[0].months < 6:
                    last_giveday = inday  # 今回付与
                    next_giveday = giveday  # 次回付与
                elif datetime.today() > giveday and monthmod(giveday, datetime.today())[0].months < 6:
                    while giveday < datetime.today():
                        giveday = giveday + relativedelta(months=12)

                    last_giveday = giveday - relativedelta(months=12)  # 今回付与
                    next_giveday = giveday  # 次回付与
                else:
                    while giveday < datetime.today():
                        giveday = giveday + relativedelta(months=12)

                    last_giveday = giveday - relativedelta(months=12)  # 今回付与
                    next_giveday = giveday  # 次回付与

                ########## 基準付与日のSQLへの登録 ##########
                ##### 新規登録職員 #####
                if rp_holiday.LAST_DATEGRANT is None and rp_holiday.NEXT_DATEGRANT is None:  # 新規登録職員＝今回付与、次回付与のない状態
                    if last_giveday == inday:  # 新入職員＝今回付与がない場合
                        rp_holiday.STAFFID = STAFFID
                        rp_holiday.INDAY = inday
                        rp_holiday.LAST_DATEGRANT = inday
                        rp_holiday.NEXT_DATEGRANT = next_giveday
                        rp_holiday.TEAM_CODE = team_code
                        rp_holiday.LNAME = lname
                        rp_holiday.FNAME = fname
                        rp_holiday.LKANA = lkana
                        rp_holiday.FKANA = fkana
                        rp_holiday.CONTRACT_CODE = contract_code
                        db.session.commit()

                        if rp_holiday.LAST_CARRIEDOVER == None:  # 前回繰越データ自体がない場合
                            rp_holiday.LAST_CARRIEDOVER = 0
                            db.session.commit()

                        if rp_holiday.USED_PAIDHOLIDAY == None:  # 使用日数データ自体がない場合
                            rp_holiday.USED_PAIDHOLIDAY = 0
                            db.session.commit()

                        if rp_holiday.REMAIN_PAIDHOLIDAY == None:  # 年休残データ自体がない場合
                            rp_holiday.REMAIN_PAIDHOLIDAY = 0
                            db.session.commit()

                    else:  # 新データ設定時、新規入職者
                        rp_holiday.LAST_DATEGRANT = last_giveday
                        rp_holiday.NEXT_DATEGRANT = next_giveday
                        db.session.commit()

                        if rp_holiday.LAST_CARRIEDOVER == None:  # 前回繰越データ自体がない場合
                            rp_holiday.LAST_CARRIEDOVER = 0
                            db.session.commit()

                        if rp_holiday.USED_PAIDHOLIDAY == None:  # 使用日数データ自体がない場合
                            rp_holiday.USED_PAIDHOLIDAY = 0
                            db.session.commit()

                        if rp_holiday.REMAIN_PAIDHOLIDAY == None:  # 年休残データ自体がない場合
                            rp_holiday.REMAIN_PAIDHOLIDAY = 0
                            db.session.commit()

                ##### 既登録職員 #####
                else:
                    rp_holiday.STAFFID = STAFFID
                    rp_holiday.INDAY = inday
                    rp_holiday.LAST_DATEGRANT = last_giveday
                    rp_holiday.NEXT_DATEGRANT = next_giveday
                    db.session.commit()

                    if rp_holiday.LAST_CARRIEDOVER == None:  # 前回繰越データ自体がない場合
                        rp_holiday.LAST_CARRIEDOVER = 0
                        db.session.commit()

                    if rp_holiday.USED_PAIDHOLIDAY == None:  # 使用日数データ自体がない場合
                        rp_holiday.USED_PAIDHOLIDAY = 0
                        db.session.commit()

                    if rp_holiday.REMAIN_PAIDHOLIDAY == None:  # 年休残データ自体がない場合
                        rp_holiday.REMAIN_PAIDHOLIDAY = 0
                        db.session.commit()

                    ##### 今回付与日数（本日ベース） #####
                    inday = rp_holiday.INDAY
                    ddm = monthmod(inday, datetime.today())[0].months
                    dm = monthmod(inday, last_giveday)[0].months

                    ##### 常勤 #####
                    if rp_holiday.CONTRACT_CODE != 2:
                        if inday.month == 4 or inday.month == 10:
                            if ddm < 6:
                                aquisition_days = 2
                            elif ddm < 12:
                                aquisition_days = 10
                            elif dm < 24:
                                aquisition_days = 11
                            elif dm < 36:
                                aquisition_days = 12
                            elif dm < 48:
                                aquisition_days = 14
                            elif dm < 60:
                                aquisition_days = 16
                            elif dm < 72:
                                aquisition_days = 18
                            elif dm >= 72:
                                aquisition_days = 20
                        elif inday.month == 5 or inday.month == 11:
                            if ddm < 5:
                                aquisition_days = 2
                            elif ddm < 11:
                                aquisition_days = 10 
                            elif dm < 23:
                                aquisition_days = 11
                            elif dm < 35:
                                aquisition_days = 12
                            elif dm < 47:
                                aquisition_days = 14
                            elif dm < 59:
                                aquisition_days = 16
                            elif dm < 71:
                                aquisition_days = 18
                            elif dm >= 71:
                                aquisition_days = 20                
                        elif inday.month == 6 or inday.month == 12:
                            if ddm < 4:
                                aquisition_days = 1
                            elif ddm < 10:
                                aquisition_days = 10 
                            elif dm < 22:
                                aquisition_days = 11
                            elif dm < 34:
                                aquisition_days = 12
                            elif dm < 46:
                                aquisition_days = 14
                            elif dm < 58:
                                aquisition_days = 16
                            elif dm < 70:
                                aquisition_days = 18
                            elif dm >= 70:
                                aquisition_days = 20            
                        elif inday.month == 7 or inday.month == 1:
                            if ddm < 3:
                                aquisition_days = 1
                            elif ddm < 9:
                                aquisition_days = 10 
                            elif dm < 21:
                                aquisition_days = 11
                            elif dm < 33:
                                aquisition_days = 12
                            elif dm < 45:
                                aquisition_days = 14
                            elif dm < 57:
                                aquisition_days = 16
                            elif dm < 69:
                                aquisition_days = 18
                            elif dm >= 69:
                                aquisition_days = 20             
                        elif inday.month == 8 or inday.month == 2:
                            if ddm < 2:
                                aquisition_days = 0
                            elif ddm < 8:
                                aquisition_days = 10 
                            elif dm < 20:
                                aquisition_days = 11
                            elif dm < 32:
                                aquisition_days = 12
                            elif dm < 44:
                                aquisition_days = 14
                            elif dm < 56:
                                aquisition_days = 16
                            elif dm < 68:
                                aquisition_days = 18
                            elif dm >= 68:
                                aquisition_days = 20                                     
                        elif inday.month == 9 or inday.month == 3:
                            if ddm < 1:
                                aquisition_days = 0
                            elif ddm < 7:
                                aquisition_days = 10 
                            elif dm < 19:
                                aquisition_days = 11
                            elif dm < 31:
                                aquisition_days = 12
                            elif dm < 43:
                                aquisition_days = 14
                            elif dm < 55:
                                aquisition_days = 16
                            elif dm < 67:
                                aquisition_days = 18
                            elif dm >= 67:
                                aquisition_days = 20

                        ##### 繰越残日数２年消滅設定 #####
                        if monthmod(inday, datetime.today())[0].months == 24 and rp_holiday.REMAIN_PAIDHOLIDAY >= 12:
                            rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 0
                        elif dm < 30 and rp_holiday.REMAIN_PAIDHOLIDAY >= 21:
                            rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 10
                        elif dm < 42 and rp_holiday.REMAIN_PAIDHOLIDAY >= 23:
                            rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 11
                        elif dm < 54 and rp_holiday.REMAIN_PAIDHOLIDAY >= 26:
                            rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 12
                        elif dm < 66 and rp_holiday.REMAIN_PAIDHOLIDAY >= 30:
                            rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 14
                        elif dm < 78 and rp_holiday.REMAIN_PAIDHOLIDAY >= 34:
                            rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 16
                        elif dm < 90 and rp_holiday.REMAIN_PAIDHOLIDAY >= 38:
                            rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 18
                        elif dm >= 90 and rp_holiday.REMAIN_PAIDHOLIDAY >= 40:
                            rp_holiday.REMAIN_PAIDHOLIDAY = rp_holiday.REMAIN_PAIDHOLIDAY - 20

                        db.session.commit()
                        enable_days = aquisition_days + rp_holiday.LAST_CARRIEDOVER  # 使用可能日数


                        ##### 取得日　取得日数　年休種類 #####
                        nenkyu_all_days = 0
                        nenkyu_half_days = 0

                        for shs in shinseis:
                            if rp_holiday.LAST_DATEGRANT == "":
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= inday and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    if shs.NOTIFICATION == "3":
                                        nenkyu_all_days += 1

                                    elif shs.NOTIFICATION == "4" or shs.NOTIFICATION == "16":
                                        nenkyu_half_days += 0.5

                                    if shs.NOTIFICATION2 == "4" or shs.NOTIFICATION2 == "16":
                                        nenkyu_half_days += 0.5
                            else:
                                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                    if shs.NOTIFICATION == "3":
                                        nenkyu_all_days += 1

                                    elif shs.NOTIFICATION == "4" or shs.NOTIFICATION == "16":
                                        nenkyu_half_days += 0.5

                                    if shs.NOTIFICATION2 == "4" or shs.NOTIFICATION2 == "16":
                                        nenkyu_half_days += 0.5

                        a = nenkyu_all_days + nenkyu_half_days  # 年休使用日数

                        b = rp_holiday.LAST_CARRIEDOVER + aquisition_days - a  # 年休残日数

                        rp_holiday.USED_PAIDHOLIDAY = a
                        rp_holiday.REMAIN_PAIDHOLIDAY = b
                        db.session.commit()

                    ##### パート #####
                    elif rp_holiday.CONTRACT_CODE == 2:

                        ##### 取得日　取得日数　年休種類 #####
                        p_nenkyu_all_days = 0
                        p_nenkyu_half_days = 0

                        for shs in shinseis:
                            if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                                if shs.NOTIFICATION == "3":
                                    p_nenkyu_all_days += 1

                                elif shs.NOTIFICATION == "4" or shs.NOTIFICATION == "16":
                                    p_nenkyu_half_days += 0.5

                                if shs.NOTIFICATION2 == "4" or shs.NOTIFICATION2 == "16":
                                    p_nenkyu_half_days += 0.5

                        p_a = p_nenkyu_all_days + p_nenkyu_half_days  # 年休使用日数

                        rp_holiday.USED_PAIDHOLIDAY = p_a
                        db.session.commit()
                        
                        
    onc = []  
    onc_1 = []
    onc_2 = []
    onc_3 = []
    onc_4 = []
    onc_5 = []
    onc_6 = []
    onc_7 = []
    onc_8 = []   
    team = u.TEAM_CODE  # この職員のチームコード
    jobtype = u.JOBTYPE_CODE
    
    users = User.query.all()
    
    for user in users:
        n = user.STAFFID
        
        shins = Shinsei.query.filter(Shinsei.STAFFID==n).all()
        if shins:
            
            for shin in shins:

                ##### ２６日基準 カウント
                if m == 1:  # １月
                    d = 31
                    base_day = datetime.strptime(shin.WORKDAY, '%Y-%m-%d')
                    if datetime(y, m, 1) >= base_day and datetime(y - 1, m + 11, 25) < base_day:
                        if shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == team:
                            onc.append("cnt")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 1:
                            onc_1.append("cnt_1")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 2:
                            onc_2.append("cnt_2")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 3:
                            onc_3.append("cnt_3")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 4:
                            onc_4.append("cnt_4")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 5:
                            onc_5.append("cnt_5")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 6:
                            onc_6.append("cnt_6")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 7:
                            onc_7.append("cnt_7")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 8:
                            onc_8.append("cnt_8") 

                if m == 2:  # ２月
                    if y % 4 == 0:
                        d = 29
                    elif y % 4 != 0:
                        d = 28

                        base_day = datetime.strptime(shin.WORKDAY, '%Y-%m-%d')
                        if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:
                            if shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == team:
                                onc.append("cnt")
                            elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 1:
                                onc_1.append("cnt_1")
                            elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 2:
                                onc_2.append("cnt_2")
                            elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 3:
                                onc_3.append("cnt_3")
                            elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 4:
                                onc_4.append("cnt_4")
                            elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 5:
                                onc_5.append("cnt_5")
                            elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 6:
                                onc_6.append("cnt_6")
                            elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 7:
                                onc_7.append("cnt_7")
                            elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 8:
                                onc_8.append("cnt_8") 


                if m == 3:  # ３月
                    d = 31
                    base_day = datetime.strptime(shin.WORKDAY, '%Y-%m-%d')
                    if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:
                        # オンコール当番
                        if shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == team:
                            onc.append("cnt")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 1:
                            onc_1.append("cnt_1")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 2:
                            onc_2.append("cnt_2")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 3:
                            onc_3.append("cnt_3")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 4:
                            onc_4.append("cnt_4")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 5:
                            onc_5.append("cnt_5")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 6:
                            onc_6.append("cnt_6")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 7:
                            onc_7.append("cnt_7")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 8:
                            onc_8.append("cnt_8") 

                if m == 4:  # ４月
                    d = 30
                    base_day = datetime.strptime(shin.WORKDAY, '%Y-%m-%d')
                    if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:
                        # オンコール当番
                        if shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == team:
                            onc.append("cnt")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 1:
                            onc_1.append("cnt_1")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 2:
                            onc_2.append("cnt_2")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 3:
                            onc_3.append("cnt_3")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 4:
                            onc_4.append("cnt_4")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 5:
                            onc_5.append("cnt_5")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 6:
                            onc_6.append("cnt_6")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 7:
                            onc_7.append("cnt_7")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 8:
                            onc_8.append("cnt_8") 

                if m == 5:  # ５月
                    d = 31
                    base_day = datetime.strptime(shin.WORKDAY, '%Y-%m-%d')
                    if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:
                        # オンコール当番
                        if shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == team:
                            onc.append("cnt")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 1:
                            onc_1.append("cnt_1")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 2:
                            onc_2.append("cnt_2")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 3:
                            onc_3.append("cnt_3")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 4:
                            onc_4.append("cnt_4")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 5:
                            onc_5.append("cnt_5")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 6:
                            onc_6.append("cnt_6")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 7:
                            onc_7.append("cnt_7")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 8:
                            onc_8.append("cnt_8") 

                if m == 6:  # ６月
                    d = 30
                    base_day = datetime.strptime(shin.WORKDAY, '%Y-%m-%d')
                    if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:
                        # オンコール当番
                        if shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == team:
                            onc.append("cnt")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 1:
                            onc_1.append("cnt_1")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 2:
                            onc_2.append("cnt_2")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 3:
                            onc_3.append("cnt_3")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 4:
                            onc_4.append("cnt_4")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 5:
                            onc_5.append("cnt_5")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 6:
                            onc_6.append("cnt_6")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 7:
                            onc_7.append("cnt_7")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 8:
                            onc_8.append("cnt_8") 

                if m == 7:  # ７月
                    d = 31
                    base_day = datetime.strptime(shin.WORKDAY, '%Y-%m-%d')
                    if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:
                        # オンコール当番
                        if shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == team:
                            onc.append("cnt")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 1:
                            onc_1.append("cnt_1")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 2:
                            onc_2.append("cnt_2")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 3:
                            onc_3.append("cnt_3")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 4:
                            onc_4.append("cnt_4")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 5:
                            onc_5.append("cnt_5")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 6:
                            onc_6.append("cnt_6")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 7:
                            onc_7.append("cnt_7")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 8:
                            onc_8.append("cnt_8") 

                if m == 8:  # ８月
                    d = 31
                    base_day = datetime.strptime(shin.WORKDAY, '%Y-%m-%d')
                    if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:
                        # オンコール当番
                        if shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == team:
                            onc.append("cnt")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 1:
                            onc_1.append("cnt_1")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 2:
                            onc_2.append("cnt_2")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 3:
                            onc_3.append("cnt_3")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 4:
                            onc_4.append("cnt_4")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 5:
                            onc_5.append("cnt_5")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 6:
                            onc_6.append("cnt_6")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 7:
                            onc_7.append("cnt_7")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 8:
                            onc_8.append("cnt_8") 

                if m == 9:  # ９月
                    d = 30
                    base_day = datetime.strptime(shin.WORKDAY, '%Y-%m-%d')
                    if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:
                        # オンコール当番
                        if shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == team:
                            onc.append("cnt")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 1:
                            onc_1.append("cnt_1")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 2:
                            onc_2.append("cnt_2")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 3:
                            onc_3.append("cnt_3")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 4:
                            onc_4.append("cnt_4")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 5:
                            onc_5.append("cnt_5")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 6:
                            onc_6.append("cnt_6")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 7:
                            onc_7.append("cnt_7")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 8:
                            onc_8.append("cnt_8") 

                if m == 10:  # １０月
                    d = 31
                    base_day = datetime.strptime(shin.WORKDAY, '%Y-%m-%d')
                    if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:
                        # オンコール当番
                        if shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == team:
                            onc.append("cnt")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 1:
                            onc_1.append("cnt_1")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 2:
                            onc_2.append("cnt_2")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 3:
                            onc_3.append("cnt_3")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 4:
                            onc_4.append("cnt_4")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 5:
                            onc_5.append("cnt_5")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 6:
                            onc_6.append("cnt_6")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 7:
                            onc_7.append("cnt_7")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 8:
                            onc_8.append("cnt_8") 

                if m == 11:  # １１月
                    d = 30
                    base_day = datetime.strptime(shin.WORKDAY, '%Y-%m-%d')
                    if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:
                        # オンコール当番
                        if shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == team:
                                onc.append("cnt")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 1:
                            onc_1.append("cnt_1")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 2:
                            onc_2.append("cnt_2")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 3:
                            onc_3.append("cnt_3")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 4:
                            onc_4.append("cnt_4")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 5:
                            onc_5.append("cnt_5")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 6:
                            onc_6.append("cnt_6")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 7:
                            onc_7.append("cnt_7")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 8:
                            onc_8.append("cnt_8") 

                if m == 12:  # １２月
                    d = 31
                    base_day = datetime.strptime(shin.WORKDAY, '%Y-%m-%d')
                    if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:
                        # オンコール当番
                        if shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == team:
                            onc.append("cnt")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 1:
                            onc_1.append("cnt_1")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 2:
                            onc_2.append("cnt_2")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 3:
                            onc_3.append("cnt_3")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 4:
                            onc_4.append("cnt_4")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 5:
                            onc_5.append("cnt_5")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 6:
                            onc_6.append("cnt_6")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 7:
                            onc_7.append("cnt_7")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 8:
                            onc_8.append("cnt_8") 

    length_oncall = len(onc)                        
    length_oncall_1 = len(onc_1)    
    length_oncall_2 = len(onc_2)
    length_oncall_3 = len(onc_3)                                
    length_oncall_4 = len(onc_4)
    length_oncall_5 = len(onc_5)    
    length_oncall_6 = len(onc_6)    
    length_oncall_7 = len(onc_7)
    length_oncall_8 = len(onc_8)                         
                
    
    reload_y = ""
    ##### 紐づけ #####
    form = EditForm()
    if form.validate_on_submit():
    
        reload_y = request.form.get('reload_h')
        ##### データ取得 #####
        i = 0
        for c in cal:
            data0 = request.form.get('dat' + str(i)) # フラッグID
            data1 = request.form.get('row' + str(i)) # 日付
            data2 = request.form.get('stime' + str(i)) # 開始時間
            data3 = request.form.get('ftime' + str(i)) # 終了時間
            data_4 = request.form.get('skyori' + str(i)) # 移動距離
            data5 = request.form.get('oncall' + str(i)) # オンコール
            data6 = request.form.get('oncall_cnt' + str(i)) # オンコール回数
            data7 = request.form.get('todokede' + str(i)) # 届出AM
            data8 = request.form.get('zangyou' + str(i)) # 残業
            data9 = request.form.get('engel' + str(i)) # エンゼル回数
            data10 = request.form.get('bikou' + str(i)) # 備考
            data11 = request.form.get('todokede_pm' + str(i)) # 届出PM            

            ##### 勤怠条件分け #####                         
            atd = AttendanceAdminAnalysys(c, STAFFID, data0, data1, data2, data3, data_4, data5, data6, data7, data8, data9, data10, data11)            
            atd.analysys()
            
            i = i + 1


        ##### 年間月別勤務時間・日数関係　常勤 ###############
        shinseis = Shinsei.query.filter_by(STAFFID=STAFFID).all()
        u = User.query.get(STAFFID)
        rp_holiday = RecordPaidHoliday.query.get(STAFFID)
        tm_attendance = TimeAttendance.query.get(STAFFID)
        cnt_attemdance = CountAttendance.query.get(STAFFID)
        
        # 各表示初期値
        oncall = []
        oncall_holiday = []
        oncall_cnt = []
        engel_cnt = []

        nenkyu = []
        nenkyu_half = []
        tikoku = []
        soutai = []
        kekkin = []
        syuttyou = []
        syuttyou_half = []
        reflesh = []
        s_kyori = []

        syukkin_times_0 = []
        syukkin_holiday_times_0 = []
        over_time_0 = []

        if u.CONTRACT_CODE != 2:
            for sh in shinseis:

                    ##### 月間実働時間（２６日基準） #####                  

                    if m == 1:  # １月
                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if datetime(y, m, 1) >= base_day and datetime(y - 1, m + 11, 25) < base_day:
                            dtm = datetime.strptime(
                                sh.ENDTIME, '%H:%M') - datetime.strptime(sh.STARTTIME, '%H:%M')

                            if u.CONTRACT_CODE != 2 and u.JOBTYPE_CODE == 1:
                                if sh.HOLIDAY == "2":                           
                                    set_hol_time = CalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                        u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    set_hol_time.calc_hol_time()
                                else:
                                    settime = CalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                            u.CONTRACT_CODE, syukkin_times_0, over_time_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    settime.calc_time()
                            else:                      
                                if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":                           
                                    set_hol_time = CalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                        u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    set_hol_time.calc_hol_time()
                                else:
                                    settime = CalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                            u.CONTRACT_CODE, syukkin_times_0, over_time_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    settime.calc_time()

                    if m == 2:  # ２月
                        if y % 4 == 0:
                            d = 29
                        elif y % 4 != 0:
                            d = 28

                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:
                            dtm = datetime.strptime(
                                sh.ENDTIME, '%H:%M') - datetime.strptime(sh.STARTTIME, '%H:%M')

                            if u.CONTRACT_CODE != 2 and u.JOBTYPE_CODE == 1:
                                if sh.HOLIDAY == "2":                           
                                    set_hol_time = CalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                        u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    set_hol_time.calc_hol_time()
                                else:
                                    settime = CalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                            u.CONTRACT_CODE, syukkin_times_0, over_time_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    settime.calc_time()
                            else:                      
                                if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":                           
                                    set_hol_time = CalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                        u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    set_hol_time.calc_hol_time()
                                else:
                                    settime = CalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                            u.CONTRACT_CODE, syukkin_times_0, over_time_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    settime.calc_time()

                    elif m == 3:  # ３月
                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:
                            dtm = datetime.strptime(
                                sh.ENDTIME, '%H:%M') - datetime.strptime(sh.STARTTIME, '%H:%M')

                            if u.CONTRACT_CODE != 2 and u.JOBTYPE_CODE == 1:
                                if sh.HOLIDAY == "2":                           
                                    set_hol_time = CalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                        u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    set_hol_time.calc_hol_time()
                                else:
                                    settime = CalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                            u.CONTRACT_CODE, syukkin_times_0, over_time_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    settime.calc_time()
                            else:                      
                                if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":                           
                                    set_hol_time = CalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                        u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    set_hol_time.calc_hol_time()
                                else:
                                    settime = CalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                            u.CONTRACT_CODE, syukkin_times_0, over_time_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    settime.calc_time()

                    elif m == 4:  # ４月
                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:
                            dtm = datetime.strptime(
                                sh.ENDTIME, '%H:%M') - datetime.strptime(sh.STARTTIME, '%H:%M')

                            if u.CONTRACT_CODE != 2 and u.JOBTYPE_CODE == 1:
                                if sh.HOLIDAY == "2":                           
                                    set_hol_time = CalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                        u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    set_hol_time.calc_hol_time()
                                else:
                                    settime = CalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                            u.CONTRACT_CODE, syukkin_times_0, over_time_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    settime.calc_time()
                            else:                      
                                if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":                           
                                    set_hol_time = CalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                        u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    set_hol_time.calc_hol_time()
                                else:
                                    settime = CalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                            u.CONTRACT_CODE, syukkin_times_0, over_time_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    settime.calc_time()

                    elif m == 5:  # ５月
                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:
                            dtm = datetime.strptime(
                                sh.ENDTIME, '%H:%M') - datetime.strptime(sh.STARTTIME, '%H:%M')

                            if u.CONTRACT_CODE != 2 and u.JOBTYPE_CODE == 1:
                                if sh.HOLIDAY == "2":                           
                                    set_hol_time = CalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                        u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    set_hol_time.calc_hol_time()
                                else:
                                    settime = CalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                            u.CONTRACT_CODE, syukkin_times_0, over_time_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    settime.calc_time()
                            else:                      
                                if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":                           
                                    set_hol_time = CalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                        u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    set_hol_time.calc_hol_time()
                                else:
                                    settime = CalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                            u.CONTRACT_CODE, syukkin_times_0, over_time_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    settime.calc_time()

                    elif m == 6:  # ６月
                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:
                            dtm = datetime.strptime(
                                sh.ENDTIME, '%H:%M') - datetime.strptime(sh.STARTTIME, '%H:%M')

                            if u.CONTRACT_CODE != 2 and u.JOBTYPE_CODE == 1:
                                if sh.HOLIDAY == "2":                           
                                    set_hol_time = CalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                        u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    set_hol_time.calc_hol_time()
                                else:
                                    settime = CalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                            u.CONTRACT_CODE, syukkin_times_0, over_time_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    settime.calc_time()
                            else:                      
                                if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":                           
                                    set_hol_time = CalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                        u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    set_hol_time.calc_hol_time()
                                else:
                                    settime = CalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                            u.CONTRACT_CODE, syukkin_times_0, over_time_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    settime.calc_time()

                    elif m == 7:  # ７月
                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:
                            dtm = datetime.strptime(
                                sh.ENDTIME, '%H:%M') - datetime.strptime(sh.STARTTIME, '%H:%M')

                            if u.CONTRACT_CODE != 2 and u.JOBTYPE_CODE == 1:
                                if sh.HOLIDAY == "2":                           
                                    set_hol_time = CalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                        u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    set_hol_time.calc_hol_time()
                                else:
                                    settime = CalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                            u.CONTRACT_CODE, syukkin_times_0, over_time_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    settime.calc_time()
                            else:                      
                                if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":                           
                                    set_hol_time = CalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                        u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    set_hol_time.calc_hol_time()
                                else:
                                    settime = CalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                            u.CONTRACT_CODE, syukkin_times_0, over_time_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    settime.calc_time()

                    elif m == 8:  # ８月
                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:
                            dtm = datetime.strptime(
                                sh.ENDTIME, '%H:%M') - datetime.strptime(sh.STARTTIME, '%H:%M')

                            if u.CONTRACT_CODE != 2 and u.JOBTYPE_CODE == 1:
                                if sh.HOLIDAY == "2":                           
                                    set_hol_time = CalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                        u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    set_hol_time.calc_hol_time()
                                else:
                                    settime = CalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                            u.CONTRACT_CODE, syukkin_times_0, over_time_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    settime.calc_time()
                            else:                      
                                if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":                           
                                    set_hol_time = CalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                        u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    set_hol_time.calc_hol_time()
                                else:
                                    settime = CalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                            u.CONTRACT_CODE, syukkin_times_0, over_time_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    settime.calc_time()

                    elif m == 9:  # ９月
                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:
                            dtm = datetime.strptime(
                                sh.ENDTIME, '%H:%M') - datetime.strptime(sh.STARTTIME, '%H:%M')

                            if u.CONTRACT_CODE != 2 and u.JOBTYPE_CODE == 1:
                                if sh.HOLIDAY == "2":                           
                                    set_hol_time = CalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                        u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    set_hol_time.calc_hol_time()
                                else:
                                    settime = CalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                            u.CONTRACT_CODE, syukkin_times_0, over_time_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    settime.calc_time()
                            else:                      
                                if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":                           
                                    set_hol_time = CalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                        u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    set_hol_time.calc_hol_time()
                                else:
                                    settime = CalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                            u.CONTRACT_CODE, syukkin_times_0, over_time_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    settime.calc_time()

                    elif m == 10:  # １０月
                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:
                            dtm = datetime.strptime(
                                sh.ENDTIME, '%H:%M') - datetime.strptime(sh.STARTTIME, '%H:%M')

                            if u.CONTRACT_CODE != 2 and u.JOBTYPE_CODE == 1:
                                if sh.HOLIDAY == "2":                           
                                    set_hol_time = CalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                        u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    set_hol_time.calc_hol_time()
                                else:
                                    settime = CalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                            u.CONTRACT_CODE, syukkin_times_0, over_time_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    settime.calc_time()
                            else:                      
                                if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":                           
                                    set_hol_time = CalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                        u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    set_hol_time.calc_hol_time()
                                else:
                                    settime = CalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                            u.CONTRACT_CODE, syukkin_times_0, over_time_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    settime.calc_time()

                    elif m == 11:  # １１月
                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:
                            dtm = datetime.strptime(
                                sh.ENDTIME, '%H:%M') - datetime.strptime(sh.STARTTIME, '%H:%M')

                            if u.CONTRACT_CODE != 2 and u.JOBTYPE_CODE == 1:
                                if sh.HOLIDAY == "2":                           
                                    set_hol_time = CalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                        u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    set_hol_time.calc_hol_time()
                                else:
                                    settime = CalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                            u.CONTRACT_CODE, syukkin_times_0, over_time_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    settime.calc_time()
                            else:                      
                                if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":                           
                                    set_hol_time = CalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                        u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    set_hol_time.calc_hol_time()
                                else:
                                    settime = CalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                            u.CONTRACT_CODE, syukkin_times_0, over_time_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    settime.calc_time()

                    elif m == 12:  # １２月
                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:

                            if u.CONTRACT_CODE != 2 and u.JOBTYPE_CODE == 1:
                                if sh.HOLIDAY == "2":                           
                                    set_hol_time = CalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                        u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    set_hol_time.calc_hol_time()
                                else:
                                    settime = CalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                            u.CONTRACT_CODE, syukkin_times_0, over_time_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    settime.calc_time()
                            else:                      
                                if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":                           
                                    set_hol_time = CalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                        u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    set_hol_time.calc_hol_time()
                                else:
                                    settime = CalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                            u.CONTRACT_CODE, syukkin_times_0, over_time_0, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                    settime.calc_time()

                    ##### ２６日基準 カウント
                    if m == 1:  # １月
                        d = 31
                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if datetime(y, m, 1) >= base_day and datetime(y - 1, m + 11, 25) < base_day:
                            if sh.ONCALL == '1':
                                oncall.append("cnt")
                                # 土日オンコール当番
                            if sh.HOLIDAY == "1":
                                oncall_holiday.append("cnt")
                            # オンコール回数
                            if sh.ONCALL_COUNT:
                                oncall_cnt.append(str(sh.ONCALL_COUNT))
                            # エンゼルケア回数
                            if sh.ENGEL_COUNT:
                                engel_cnt.append(str(sh.ENGEL_COUNT))
                            # 年休日数（全日）
                            if sh.NOTIFICATION == "3":
                                if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":
                                    pass
                                else:
                                    nenkyu.append("cnt")
                            # 年休日数（半日）
                            if sh.NOTIFICATION == "4" or sh.NOTIFICATION == "16":
                                nenkyu_half.append("cnt")
                            # 年休日数（半日）
                            if sh.NOTIFICATION2 == "4" or sh.NOTIFICATION2 == "16":
                                nenkyu_half.append("cnt")
                            # 遅刻回数
                            if sh.NOTIFICATION == "1":
                                tikoku.append("cnt")
                            # 遅刻回数
                            if sh.NOTIFICATION2 == "1":
                                tikoku.append("cnt")
                            # 早退回数
                            if sh.NOTIFICATION == "2":
                                soutai.append("cnt")
                            # 早退回数
                            if sh.NOTIFICATION2 == "2":
                                soutai.append("cnt")
                            # 欠勤日数
                            if sh.NOTIFICATION == "8" or sh.NOTIFICATION == "17" or sh.NOTIFICATION == "18" or sh.NOTIFICATION == "19" or sh.NOTIFICATION == "20":
                                if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":
                                    pass
                                else:
                                    kekkin.append("cnt")
                            # 出張（全日）回数
                            if sh.NOTIFICATION == "5":
                                syuttyou.append("cnt")
                            # 出張（半日）回数
                            if sh.NOTIFICATION == "6":
                                syuttyou_half.append("cnt")
                            # 出張（半日）回数
                            if sh.NOTIFICATION2 == "6":
                                syuttyou_half.append("cnt")
                            # リフレッシュ休暇日数
                            if sh.NOTIFICATION == "7":
                                if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":
                                    pass
                                else:
                                    reflesh.append("cnt")
                            # 走行距離
                            if sh.MILEAGE:
                                s_kyori.append(str(sh.MILEAGE))

                    if m == 2:  # ２月
                        if y % 4 == 0:
                            d = 29
                        elif y % 4 != 0:
                            d = 28

                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:
                            if sh.ONCALL == '1':
                                oncall.append("cnt")
                                # 土日オンコール当番
                            if sh.HOLIDAY == "1":
                                oncall_holiday.append("cnt")
                            # オンコール回数
                            if sh.ONCALL_COUNT:
                                oncall_cnt.append(str(sh.ONCALL_COUNT))
                            # エンゼルケア回数
                            if sh.ENGEL_COUNT:
                                engel_cnt.append(str(sh.ENGEL_COUNT))
                            # 年休日数（全日）
                            if sh.NOTIFICATION == "3":
                                if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":
                                    pass
                                else:
                                    nenkyu.append("cnt")
                            # 年休日数（半日）
                            if sh.NOTIFICATION == "4" or sh.NOTIFICATION == "16":
                                nenkyu_half.append("cnt")
                            # 年休日数（半日）
                            if sh.NOTIFICATION2 == "4" or sh.NOTIFICATION2 == "16":
                                nenkyu_half.append("cnt")
                            # 遅刻回数
                            if sh.NOTIFICATION == "1":
                                tikoku.append("cnt")
                            # 遅刻回数
                            if sh.NOTIFICATION2 == "1":
                                tikoku.append("cnt")
                            # 早退回数
                            if sh.NOTIFICATION == "2":
                                soutai.append("cnt")
                            # 早退回数
                            if sh.NOTIFICATION2 == "2":
                                soutai.append("cnt")
                            # 欠勤日数
                            if sh.NOTIFICATION == "8" or sh.NOTIFICATION == "17" or sh.NOTIFICATION == "18" or sh.NOTIFICATION == "19" or sh.NOTIFICATION == "20":
                                if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":
                                    pass
                                else:
                                    kekkin.append("cnt")
                            # 出張（全日）回数
                            if sh.NOTIFICATION == "5":
                                syuttyou.append("cnt")
                            # 出張（半日）回数
                            if sh.NOTIFICATION == "6":
                                syuttyou_half.append("cnt")
                            # 出張（半日）回数
                            if sh.NOTIFICATION2 == "6":
                                syuttyou_half.append("cnt")
                            # リフレッシュ休暇日数
                            if sh.NOTIFICATION == "7":
                                if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":
                                    pass
                                else:
                                    reflesh.append("cnt")
                            # 走行距離
                            if sh.MILEAGE:
                                s_kyori.append(str(sh.MILEAGE))

                    if m == 3:  # ３月
                        d = 31
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                                sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                                oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                                tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)
                        dft26.other_data26()

                    if m == 4:  # ４月
                        d = 30
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                                sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                                oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                                tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                    if m == 5:  # ５月
                        d = 31
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                                sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                                oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                                tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                    if m == 6:  # ６月
                        d = 30
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                                sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                                oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                                tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                    if m == 7:  # ７月
                        d = 31
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                                sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                                oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                                tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                    if m == 8:  # ８月
                        d = 31
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                                sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                                oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                                tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                    if m == 9:  # ９月
                        d = 30
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                                sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                                oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                                tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                    if m == 10:  # １０月
                        d = 31
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                                sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                                oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                                tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                    if m == 11:  # １１月
                        d = 30
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                                sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                                oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                                tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                    if m == 12:  # １２月
                        d = 31
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                                sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                                oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                                tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

            ##### データベース貯蔵 #####
            ln_oncall = len(oncall)
            ln_oncall_holiday = len(oncall_holiday)
            
            ln_oncall_cnt = 0
            for oc in oncall_cnt:
                ln_oncall_cnt += int(oc)

            ln_engel_cnt = 0
            for ac in engel_cnt:
                ln_engel_cnt += int(ac)

            ln_nenkyu = len(nenkyu)
            ln_nenkyu_half = len(nenkyu_half)
            ln_tikoku = len(tikoku)
            ln_soutai = len(soutai)
            ln_kekkin = len(kekkin)
            ln_syuttyou = len(syuttyou)
            ln_syuttyou_half = len(syuttyou_half)
            ln_reflesh = len(reflesh)

            ln_s_kyori = 0
            for s in s_kyori:
                ln_s_kyori += float(s)

            sum_0 = 0
            for n in range(len(syukkin_times_0)):
                sum_0 += syukkin_times_0[n]
            w_h = sum_0 // (60 * 60)
            w_m = (sum_0 - w_h * 60 * 60) // 60
            working_time = w_h + w_m / 100
            working_time_10 = sum_0 / (60 * 60)
            
            sum_over_0 = 0
            for n in range(len(over_time_0)):
                sum_over_0 += over_time_0[n]
            o_h = sum_over_0 // (60 * 60)
            o_m = (sum_over_0 - o_h * 60 * 60) // 60                    
            over = o_h + o_m / 100
            over_10 = sum_over_0 / (60 * 60)

            sum_hol_0 = 0
            for t in syukkin_holiday_times_0:
                sum_hol_0 += t
            h_h = sum_hol_0 // (60 * 60)
            h_m = (sum_hol_0 - h_h * 60 * 60) // 60   
            holiday_work = h_h + h_m / 100
            holiday_work_10 = sum_hol_0 / (60 * 60)

            workday_count = len(syukkin_times_0)


            if m == 1:
                tm_attendance.TIME_1 = working_time
                tm_attendance.OVER_TIME_1 = over
                tm_attendance.TIME_HOLIDAY_1 = holiday_work
                db.session.commit()
                cnt_attemdance.MONTH_1 = workday_count
                cnt_attemdance.MONTH_HOLIDAY_1 = len(syukkin_holiday_times_0)         
                db.session.commit()
            elif m == 2:
                tm_attendance.TIME_2 = working_time
                tm_attendance.OVER_TIME_2 = over
                tm_attendance.TIME_HOLIDAY_2 = holiday_work
                db.session.commit()
                cnt_attemdance.MONTH_2 = workday_count
                cnt_attemdance.MONTH_HOLIDAY_2 = len(syukkin_holiday_times_0)         
                db.session.commit()
            elif m == 3:
                tm_attendance.TIME_3 = working_time
                tm_attendance.OVER_TIME_3 = over
                tm_attendance.TIME_HOLIDAY_3 = holiday_work
                db.session.commit()
                cnt_attemdance.MONTH_3 = workday_count
                cnt_attemdance.MONTH_HOLIDAY_3 = len(syukkin_holiday_times_0)         
                db.session.commit()
            elif m == 4:
                tm_attendance.TIME_4 = working_time
                tm_attendance.OVER_TIME_4 = over
                tm_attendance.TIME_HOLIDAY_4 = holiday_work
                db.session.commit()
                cnt_attemdance.MONTH_4 = workday_count
                cnt_attemdance.MONTH_HOLIDAY_4 = len(syukkin_holiday_times_0)         
                db.session.commit()
            elif m == 5:
                tm_attendance.TIME_5 = working_time
                tm_attendance.OVER_TIME_5 = over
                tm_attendance.TIME_HOLIDAY_5 = holiday_work
                db.session.commit()
                cnt_attemdance.MONTH_5 = workday_count
                cnt_attemdance.MONTH_HOLIDAY_5 = len(syukkin_holiday_times_0)         
                db.session.commit()
            elif m == 6:
                tm_attendance.TIME_6 = working_time
                tm_attendance.OVER_TIME_6 = over
                tm_attendance.TIME_HOLIDAY_6 = holiday_work
                db.session.commit()
                cnt_attemdance.MONTH_6 = workday_count
                cnt_attemdance.MONTH_HOLIDAY_6 = len(syukkin_holiday_times_0)         
                db.session.commit()
            elif m == 7:
                tm_attendance.TIME_7 = working_time
                tm_attendance.OVER_TIME_7 = over
                tm_attendance.TIME_HOLIDAY_7 = holiday_work
                db.session.commit()
                cnt_attemdance.MONTH_7 = workday_count
                cnt_attemdance.MONTH_HOLIDAY_7 = len(syukkin_holiday_times_0)         
                db.session.commit()
            elif m == 8:
                tm_attendance.TIME_8 = working_time
                tm_attendance.OVER_TIME_8 = over
                tm_attendance.TIME_HOLIDAY_8 = holiday_work
                db.session.commit()
                cnt_attemdance.MONTH_8 = workday_count
                cnt_attemdance.MONTH_HOLIDAY_8 = len(syukkin_holiday_times_0)         
                db.session.commit()
            elif m == 9:
                tm_attendance.TIME_9 = working_time
                tm_attendance.OVER_TIME_9 = over
                tm_attendance.TIME_HOLIDAY_9 = holiday_work
                db.session.commit()
                cnt_attemdance.MONTH_9 = workday_count
                cnt_attemdance.MONTH_HOLIDAY_9 = len(syukkin_holiday_times_0)         
                db.session.commit()
            elif m == 10:
                tm_attendance.TIME_10 = working_time
                tm_attendance.OVER_TIME_10 = over
                tm_attendance.TIME_HOLIDAY_10 = holiday_work
                db.session.commit()
                cnt_attemdance.MONTH_10 = workday_count
                cnt_attemdance.MONTH_HOLIDAY_10 = len(syukkin_holiday_times_0)         
                db.session.commit()
            elif m == 11:
                tm_attendance.TIME_11 = working_time
                tm_attendance.OVER_TIME_11 = over
                tm_attendance.TIME_HOLIDAY_11 = holiday_work
                db.session.commit()
                cnt_attemdance.MONTH_11 = workday_count
                cnt_attemdance.MONTH_HOLIDAY_11 = len(syukkin_holiday_times_0)         
                db.session.commit()
            elif m == 12:
                tm_attendance.TIME_12 = working_time
                tm_attendance.OVER_TIME_12 = over
                tm_attendance.TIME_HOLIDAY_12 = holiday_work
                db.session.commit()
                cnt_attemdance.MONTH_12 = workday_count
                cnt_attemdance.MONTH_HOLIDAY_12 = len(syukkin_holiday_times_0)         
                db.session.commit()
            

        ##### 年間月別勤務時間・日数関係　パート ###############            
        shinseis = Shinsei.query.filter_by(STAFFID=STAFFID).all()
        u = User.query.get(STAFFID)
        rp_holiday = RecordPaidHoliday.query.get(STAFFID)
        tm_attendance = TimeAttendance.query.get(STAFFID)
        cnt_attemdance = CountAttendance.query.get(STAFFID)
            
        # 各表示初期値
        oncall = []
        oncall_holiday = []
        oncall_cnt = []
        engel_cnt = []

        nenkyu = []
        nenkyu_half = []
        tikoku = []
        soutai = []
        kekkin = []
        syuttyou = []
        syuttyou_half = []
        reflesh = []
        s_kyori = []

        syukkin_times_0 = []
        syukkin_holiday_times_0 = []
        over_time_0 = []

        if u.CONTRACT_CODE == 2:
            for sh in shinseis:
                if u.CONTRACT_CODE == 2:

                    ##### 月間実働時間（２６日基準） #####
                    if m == 1:  # 1月
                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if datetime(y, m, 1) >= base_day and datetime(y - 1, m + 11, 25) < base_day:
                            dtm = datetime.strptime(
                                sh.ENDTIME, '%H:%M') - datetime.strptime(sh.STARTTIME, '%H:%M')

                            if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":
                                set_hol_time = PartCalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                    u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0,
                                                                    rp_holiday.WORK_TIME, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                set_hol_time.calc_hol_time()
                            else:
                                settime = PartCalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                        u.CONTRACT_CODE, syukkin_times_0, over_time_0,
                                                        rp_holiday.WORK_TIME, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                settime.calc_time()

                    elif m == 2:  # ２月
                        if y % 4 == 0:
                            d = 29
                        elif y % 4 != 0:
                            d = 28

                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:
                            dtm = datetime.strptime(
                                sh.ENDTIME, '%H:%M') - datetime.strptime(sh.STARTTIME, '%H:%M')
                            if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":
                                set_hol_time = PartCalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                    u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0,
                                                                    rp_holiday.WORK_TIME, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                set_hol_time.calc_hol_time()
                            else:
                                settime = PartCalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                        u.CONTRACT_CODE, syukkin_times_0, over_time_0,
                                                        rp_holiday.WORK_TIME, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                settime.calc_time()

                    elif m == 3:  # ３月
                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:                        
                            dtm = datetime.strptime(
                                sh.ENDTIME, '%H:%M') - datetime.strptime(sh.STARTTIME, '%H:%M')

                            if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":
                                set_hol_time = PartCalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                    u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0,
                                                                    rp_holiday.WORK_TIME, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                set_hol_time.calc_hol_time()
                            else:
                                settime = PartCalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                        u.CONTRACT_CODE, syukkin_times_0, over_time_0,
                                                        rp_holiday.WORK_TIME, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                settime.calc_time()

                    elif m == 4:  # ４月
                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:                        
                        
                            dtm = datetime.strptime(
                                sh.ENDTIME, '%H:%M') - datetime.strptime(sh.STARTTIME, '%H:%M')

                            if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":
                                set_hol_time = PartCalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                    u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0,
                                                                    rp_holiday.WORK_TIME, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                set_hol_time.calc_hol_time()
                            else:
                                settime = PartCalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                        u.CONTRACT_CODE, syukkin_times_0, over_time_0,
                                                        rp_holiday.WORK_TIME, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                settime.calc_time()

                    elif m == 5:  # ５月
                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:                        
                        
                            dtm = datetime.strptime(
                                sh.ENDTIME, '%H:%M') - datetime.strptime(sh.STARTTIME, '%H:%M')

                            if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":
                                set_hol_time = PartCalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                    u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0,
                                                                    rp_holiday.WORK_TIME, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                set_hol_time.calc_hol_time()
                            else:
                                settime = PartCalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                        u.CONTRACT_CODE, syukkin_times_0, over_time_0,
                                                        rp_holiday.WORK_TIME, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                settime.calc_time()

                    elif m == 6:  # ６月
                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:                        
                        
                            dtm = datetime.strptime(
                                sh.ENDTIME, '%H:%M') - datetime.strptime(sh.STARTTIME, '%H:%M')

                            if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":
                                set_hol_time = PartCalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                    u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0,
                                                                    rp_holiday.WORK_TIME, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                set_hol_time.calc_hol_time()
                            else:
                                settime = PartCalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                        u.CONTRACT_CODE, syukkin_times_0, over_time_0,
                                                        rp_holiday.WORK_TIME, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                settime.calc_time()

                    elif m == 7:  # ７月
                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:                        
                        
                            dtm = datetime.strptime(
                                sh.ENDTIME, '%H:%M') - datetime.strptime(sh.STARTTIME, '%H:%M')

                            if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":
                                set_hol_time = PartCalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                    u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0,
                                                                    rp_holiday.WORK_TIME, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                set_hol_time.calc_hol_time()
                            else:
                                settime = PartCalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                        u.CONTRACT_CODE, syukkin_times_0, over_time_0,
                                                        rp_holiday.WORK_TIME, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                settime.calc_time()

                    elif m == 8:  # ８月
                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:                        
                        
                            dtm = datetime.strptime(
                                sh.ENDTIME, '%H:%M') - datetime.strptime(sh.STARTTIME, '%H:%M')

                            if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":
                                set_hol_time = PartCalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                    u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0,
                                                                    rp_holiday.WORK_TIME, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                set_hol_time.calc_hol_time()
                            else:
                                settime = PartCalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                        u.CONTRACT_CODE, syukkin_times_0, over_time_0,
                                                        rp_holiday.WORK_TIME, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                settime.calc_time()

                    elif m == 9:  # ９月
                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:                        
                        
                            dtm = datetime.strptime(
                                sh.ENDTIME, '%H:%M') - datetime.strptime(sh.STARTTIME, '%H:%M')

                            if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":
                                set_hol_time = PartCalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                    u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0,
                                                                    rp_holiday.WORK_TIME, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                set_hol_time.calc_hol_time()
                            else:
                                settime = PartCalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                        u.CONTRACT_CODE, syukkin_times_0, over_time_0,
                                                        rp_holiday.WORK_TIME, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                settime.calc_time()

                    elif m == 10:  # １０月
                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:                        
                        
                            dtm = datetime.strptime(
                                sh.ENDTIME, '%H:%M') - datetime.strptime(sh.STARTTIME, '%H:%M')

                            if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":
                                set_hol_time = PartCalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                    u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0,
                                                                    rp_holiday.WORK_TIME, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                set_hol_time.calc_hol_time()
                            else:
                                settime = PartCalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                        u.CONTRACT_CODE, syukkin_times_0, over_time_0,
                                                        rp_holiday.WORK_TIME, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                settime.calc_time()

                    elif m == 11:  # １１月
                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:                        
                        
                            dtm = datetime.strptime(
                                sh.ENDTIME, '%H:%M') - datetime.strptime(sh.STARTTIME, '%H:%M')

                            if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":
                                set_hol_time = PartCalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                    u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0,
                                                                    rp_holiday.WORK_TIME, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                set_hol_time.calc_hol_time()
                            else:
                                settime = PartCalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                        u.CONTRACT_CODE, syukkin_times_0, over_time_0,
                                                        rp_holiday.WORK_TIME, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                settime.calc_time()

                    elif m == 12:  # １２月
                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:                        
                        
                            dtm = datetime.strptime(
                                sh.ENDTIME, '%H:%M') - datetime.strptime(sh.STARTTIME, '%H:%M')

                            if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":
                                set_hol_time = PartCalcHolidayTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                                    u.CONTRACT_CODE, syukkin_holiday_times_0, over_time_0, syukkin_times_0,
                                                                    rp_holiday.WORK_TIME, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                set_hol_time.calc_hol_time()
                            else:
                                settime = PartCalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                                        u.CONTRACT_CODE, syukkin_times_0, over_time_0,
                                                        rp_holiday.WORK_TIME, rp_holiday.BASETIMES_PAIDHOLIDAY)
                                settime.calc_time()

                    ##### ２６日基準 カウント
                    if m == 1:  # １月
                        d = 31
                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if datetime(y, m, 1) >= base_day and datetime(y - 1, m + 11, 25) < base_day:
                            if sh.ONCALL == '1':
                                oncall.append("cnt")
                                # 土日オンコール当番
                            if sh.HOLIDAY == "1":
                                oncall_holiday.append("cnt")
                            # オンコール回数
                            if sh.ONCALL_COUNT:
                                oncall_cnt.append(str(sh.ONCALL_COUNT))
                            # エンゼルケア回数
                            if sh.ENGEL_COUNT:
                                engel_cnt.append(str(sh.ENGEL_COUNT))
                            # 年休日数（全日）
                            if sh.NOTIFICATION == "3":
                                if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":
                                    pass
                                else:
                                    nenkyu.append("cnt")
                            # 年休日数（半日）
                            if sh.NOTIFICATION == "4" or sh.NOTIFICATION == "16":
                                nenkyu_half.append("cnt")
                            # 年休日数（半日）
                            if sh.NOTIFICATION2 == "4" or sh.NOTIFICATION2 =="16":
                                nenkyu_half.append("cnt")
                            # 遅刻回数
                            if sh.NOTIFICATION == "1":
                                tikoku.append("cnt")
                            # 遅刻回数
                            if sh.NOTIFICATION2 == "1":
                                tikoku.append("cnt")
                            # 早退回数
                            if sh.NOTIFICATION == "2":
                                soutai.append("cnt")
                            # 早退回数
                            if sh.NOTIFICATION2 == "2":
                                soutai.append("cnt")
                            # 欠勤日数
                            if sh.NOTIFICATION == "8" or sh.NOTIFICATION == "17" or sh.NOTIFICATION == "18" or sh.NOTIFICATION == "19" or sh.NOTIFICATION == "20":
                                if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":
                                    pass
                                else:
                                    kekkin.append("cnt")
                            # 出張（全日）回数
                            if sh.NOTIFICATION == "5":
                                syuttyou.append("cnt")
                            # 出張（半日）回数
                            if sh.NOTIFICATION == "6":
                                syuttyou_half.append("cnt")
                            # 出張（半日）回数
                            if sh.NOTIFICATION2 == "6":
                                syuttyou_half.append("cnt")
                            # リフレッシュ休暇日数
                            if sh.NOTIFICATION == "7":
                                if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":
                                    pass
                                else:
                                    reflesh.append("cnt")
                            # 走行距離
                            if sh.MILEAGE:
                                s_kyori.append(str(sh.MILEAGE))

                    if m == 2:  # ２月
                        if y % 4 == 0:
                            d = 29
                        elif y % 4 != 0:
                            d = 28

                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if datetime(y, m, 25) >= base_day and datetime(y, m - 1, 25) < base_day:
                            if sh.ONCALL == '1':
                                oncall.append("cnt")
                                # 土日オンコール当番
                            if sh.HOLIDAY == "1":
                                oncall_holiday.append("cnt")
                            # オンコール回数
                            if sh.ONCALL_COUNT:
                                oncall_cnt.append(str(sh.ONCALL_COUNT))
                            # エンゼルケア回数
                            if sh.ENGEL_COUNT:
                                engel_cnt.append(str(sh.ENGEL_COUNT))
                            # 年休日数（全日）
                            if sh.NOTIFICATION == "3":
                                if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":
                                    pass
                                else:
                                    nenkyu.append("cnt")
                            # 年休日数（半日）
                            if sh.NOTIFICATION == "4" or sh.NOTIFICATION == "16":
                                nenkyu_half.append("cnt")
                            # 年休日数（半日）
                            if sh.NOTIFICATION2 == "4" or sh.NOTIFICATION2 =="16":
                                nenkyu_half.append("cnt")
                            # 遅刻回数
                            if sh.NOTIFICATION == "1":
                                tikoku.append("cnt")
                            # 遅刻回数
                            if sh.NOTIFICATION2 == "1":
                                tikoku.append("cnt")
                            # 早退回数
                            if sh.NOTIFICATION == "2":
                                soutai.append("cnt")
                            # 早退回数
                            if sh.NOTIFICATION2 == "2":
                                soutai.append("cnt")
                            # 欠勤日数
                            if sh.NOTIFICATION == "8" or sh.NOTIFICATION == "17" or sh.NOTIFICATION == "18" or sh.NOTIFICATION == "19" or sh.NOTIFICATION == "20":
                                if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":
                                    pass
                                else:
                                    kekkin.append("cnt")
                            # 出張（全日）回数
                            if sh.NOTIFICATION == "5":
                                syuttyou.append("cnt")
                            # 出張（半日）回数
                            if sh.NOTIFICATION == "6":
                                syuttyou_half.append("cnt")
                            # 出張（半日）回数
                            if sh.NOTIFICATION2 == "6":
                                syuttyou_half.append("cnt")
                            # リフレッシュ休暇日数
                            if sh.NOTIFICATION == "7":
                                if sh.HOLIDAY == "1" or sh.HOLIDAY == "2":
                                    pass
                                else:
                                    reflesh.append("cnt")
                            # 走行距離
                            if sh.MILEAGE:
                                s_kyori.append(str(sh.MILEAGE))

                    if m == 3:  # ３月
                        d = 31
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                                sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                                oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                                tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)
                        dft26.other_data26()

                    if m == 4:  # ４月
                        d = 30
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                                sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                                oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                                tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                    if m == 5:  # ５月
                        d = 31
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                                sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                                oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                                tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                    if m == 6:  # ６月
                        d = 30
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                                sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                                oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                                tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                    if m == 7:  # ７月
                        d = 31
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                                sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                                oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                                tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                    if m == 8:  # ８月
                        d = 31
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                                sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                                oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                                tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                    if m == 9:  # ９月
                        d = 30
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                                sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                                oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                                tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                    if m == 10:  # １０月
                        d = 31
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                                sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                                oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                                tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                    if m == 11:  # １１月
                        d = 30
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                                sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                                oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                                tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                    if m == 12:  # １２月
                        d = 31
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                                sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                                oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                                tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

            ##### データベース貯蔵 #####
            ln_oncall = len(oncall)
            ln_oncall_holiday = len(oncall_holiday)

            ln_oncall_cnt = 0
            for oc in oncall_cnt:
                ln_oncall_cnt += int(oc)

            ln_engel_cnt = 0
            for ac in engel_cnt:
                ln_engel_cnt += int(ac)

            ln_nenkyu = len(nenkyu)
            ln_nenkyu_half = len(nenkyu_half)
            ln_tikoku = len(tikoku)
            ln_soutai = len(soutai)
            ln_kekkin = len(kekkin)
            ln_syuttyou = len(syuttyou)
            ln_syuttyou_half = len(syuttyou_half)
            ln_reflesh = len(reflesh)

            ln_s_kyori = 0
            for s in s_kyori:
                ln_s_kyori += float(s)

            sum_0 = 0
            for n in range(len(syukkin_times_0)):
                sum_0 += syukkin_times_0[n]
            w_h = sum_0 // (60 * 60)
            w_m = (sum_0 - w_h * 60 * 60) // 60
            working_time = w_h + w_m / 100
            working_time_10 = sum_0 / (60 * 60)
            
            sum_over_0 = 0
            for n in range(len(over_time_0)):
                sum_over_0 += over_time_0[n]
            o_h = sum_over_0 // (60 * 60)
            o_m = (sum_over_0 - o_h * 60 * 60) // 60                    
            over = o_h + o_m / 100
            over_10 = sum_over_0 / (60 * 60)

            sum_hol_0 = 0
            for t in syukkin_holiday_times_0:
                sum_hol_0 += t
            h_h = sum_hol_0 // (60 * 60)
            h_m = (sum_hol_0 - h_h * 60 * 60) // 60   
            holiday_work = h_h + h_m / 100
            holiday_work_10 = sum_hol_0 / (60 * 60)

            workday_count = len(syukkin_times_0)


            if m == 1:
                tm_attendance.TIME_1 = working_time
                tm_attendance.OVER_TIME_1 = over
                tm_attendance.TIME_HOLIDAY_1 = holiday_work
                db.session.commit()
                cnt_attemdance.MONTH_1 = workday_count
                cnt_attemdance.MONTH_HOLIDAY_1 = len(syukkin_holiday_times_0)         
                db.session.commit()
            elif m == 2:
                tm_attendance.TIME_2 = working_time
                tm_attendance.OVER_TIME_2 = over
                tm_attendance.TIME_HOLIDAY_2 = holiday_work
                db.session.commit()
                cnt_attemdance.MONTH_2 = workday_count
                cnt_attemdance.MONTH_HOLIDAY_2 = len(syukkin_holiday_times_0)         
                db.session.commit()
            elif m == 3:
                tm_attendance.TIME_3 = working_time
                tm_attendance.OVER_TIME_3 = over
                tm_attendance.TIME_HOLIDAY_3 = holiday_work
                db.session.commit()
                cnt_attemdance.MONTH_3 = workday_count
                cnt_attemdance.MONTH_HOLIDAY_3 = len(syukkin_holiday_times_0)         
                db.session.commit()
            elif m == 4:
                tm_attendance.TIME_4 = working_time
                tm_attendance.OVER_TIME_4 = over
                tm_attendance.TIME_HOLIDAY_4 = holiday_work
                db.session.commit()
                cnt_attemdance.MONTH_4 = workday_count
                cnt_attemdance.MONTH_HOLIDAY_4 = len(syukkin_holiday_times_0)         
                db.session.commit()
            elif m == 5:
                tm_attendance.TIME_5 = working_time
                tm_attendance.OVER_TIME_5 = over
                tm_attendance.TIME_HOLIDAY_5 = holiday_work
                db.session.commit()
                cnt_attemdance.MONTH_5 = workday_count
                cnt_attemdance.MONTH_HOLIDAY_5 = len(syukkin_holiday_times_0)         
                db.session.commit()
            elif m == 6:
                tm_attendance.TIME_6 = working_time
                tm_attendance.OVER_TIME_6 = over
                tm_attendance.TIME_HOLIDAY_6 = holiday_work
                db.session.commit()
                cnt_attemdance.MONTH_6 = workday_count
                cnt_attemdance.MONTH_HOLIDAY_6 = len(syukkin_holiday_times_0)         
                db.session.commit()
            elif m == 7:
                tm_attendance.TIME_7 = working_time
                tm_attendance.OVER_TIME_7 = over
                tm_attendance.TIME_HOLIDAY_7 = holiday_work
                db.session.commit()
                cnt_attemdance.MONTH_7 = workday_count
                cnt_attemdance.MONTH_HOLIDAY_7 = len(syukkin_holiday_times_0)         
                db.session.commit()
            elif m == 8:
                tm_attendance.TIME_8 = working_time
                tm_attendance.OVER_TIME_8 = over
                tm_attendance.TIME_HOLIDAY_8 = holiday_work
                db.session.commit()
                cnt_attemdance.MONTH_8 = workday_count
                cnt_attemdance.MONTH_HOLIDAY_8 = len(syukkin_holiday_times_0)         
                db.session.commit()
            elif m == 9:
                tm_attendance.TIME_9 = working_time
                tm_attendance.OVER_TIME_9 = over
                tm_attendance.TIME_HOLIDAY_9 = holiday_work
                db.session.commit()
                cnt_attemdance.MONTH_9 = workday_count
                cnt_attemdance.MONTH_HOLIDAY_9 = len(syukkin_holiday_times_0)         
                db.session.commit()
            elif m == 10:
                tm_attendance.TIME_10 = working_time
                tm_attendance.OVER_TIME_10 = over
                tm_attendance.TIME_HOLIDAY_10 = holiday_work
                db.session.commit()
                cnt_attemdance.MONTH_10 = workday_count
                cnt_attemdance.MONTH_HOLIDAY_10 = len(syukkin_holiday_times_0)         
                db.session.commit()
            elif m == 11:
                tm_attendance.TIME_11 = working_time
                tm_attendance.OVER_TIME_11 = over
                tm_attendance.TIME_HOLIDAY_11 = holiday_work
                db.session.commit()
                cnt_attemdance.MONTH_11 = workday_count
                cnt_attemdance.MONTH_HOLIDAY_11 = len(syukkin_holiday_times_0)         
                db.session.commit()
            elif m == 12:
                tm_attendance.TIME_12 = working_time
                tm_attendance.OVER_TIME_12 = over
                tm_attendance.TIME_HOLIDAY_12 = holiday_work
                db.session.commit()
                cnt_attemdance.MONTH_12 = workday_count
                cnt_attemdance.MONTH_HOLIDAY_12 = len(syukkin_holiday_times_0)         
                db.session.commit()
            

    else: # 初期登録
        for c in cal:
            sh = Shinsei.query.filter(Shinsei.STAFFID==STAFFID).filter(Shinsei.WORKDAY==c.strftime('%Y-%m-%d')).first()
            if sh is None and STAFFID != 10000:
                WORKDAY = c.strftime('%Y-%m-%d')
                STARTTIME = "00:00"
                ENDTIME = "00:00"
                MILEAGE = "0.0"
                STAFFID = STAFFID
                ONCALL = 0
                ONCALL_COUNT = "0"
                NOTIFICATION = ""
                NOTIFICATION2 = ""
                OVERTIME = 0
                ENGEL_COUNT = "0"
                REMARK = ""
                HOLIDAY = ""
                sh = Shinsei(STAFFID, WORKDAY, HOLIDAY, STARTTIME, ENDTIME, MILEAGE,
                                ONCALL, ONCALL_COUNT, ENGEL_COUNT, NOTIFICATION, NOTIFICATION2, OVERTIME, REMARK)
                db.session.add(sh)
                db.session.commit()

    
    return render_template('admin/users_detail.html', title='ホーム', cal=cal, shinseis=shinseis, y=y, m=m, form=form, form_month=form_month,
                           oc=oc, oc_cnt=oc_cnt, eg=eg, sk=sk, othr=othr, hld=hld, u=u, bk=bk, tbl_clm=tbl_clm, typ=typ, ptn=ptn,
                           specification=specification, wk=wk, td1=td1, td2=td2, td3=td3, td4=td4, td5=td5, td6=td6, td7=td7,
                           td8=td8, td9=td9, td10=td10, td11=td11, td12=td12, td13=td13, td14=td14, td15=td15, td16=td16,
                           workday_data=workday_data, rp_holiday=rp_holiday, cnt_attemdance=cnt_attemdance, reload_y=reload_y,
                           td17=td17, td18=td18, td19=td19, td20=td20, length_oncall=length_oncall, team=team, jobtype=jobtype, length_oncall_1=length_oncall_1, length_oncall_2=length_oncall_2,
                           length_oncall_3=length_oncall_3, length_oncall_4=length_oncall_4, length_oncall_5=length_oncall_5,
                           length_oncall_6=length_oncall_6, length_oncall_7=length_oncall_7, length_oncall_8=length_oncall_8,
                           team_name=team_name, stf_login=stf_login)

       
        
@ app.route('/admin/index_select_detail_admin/<STAFFID>', methods=['GET', 'POST'])
@ login_required
@ admin_login_required
def index_select_detail_admin(STAFFID):
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    shinseis = Shinsei.query.filter_by(STAFFID=STAFFID).all()
    STAFFID = STAFFID
    shin = Shinsei.query.filter_by(STAFFID=STAFFID)
    u = User.query.get(STAFFID)
            
    ##### index表示関連 #####
    form_month = SelectMonthForm()
    form = EditForm()
    
    tbl_clm = ["日付", "曜日", "oncall", "oncall対応件数", "engel対応件数",
               "開始時間", "終了時間", "走行距離", "届出（午前）", "残業申請", "備考", "届出（午後）"]
    wk = ["日", "土", "月", "火", "水", "木", "金"]
    ptn = ["^[0-9０-９]+$", "^[0-9.０-９．]+$"]
    specification = ["readonly", "checked", "selected", "hidden"]
    typ = ["submit", "text", "time", "checkbox", "number", "date"]
    team_name = ["本社", "WADEWADE訪問看護ステーション宇都宮", "WADEWADE訪問看護ステーション下野", "WADEWADE訪問看護ステーション鹿沼",
                 "KODOMOTOナースステーションうつのみや", "わでわで在宅支援センターうつのみや", "わでわで子どもそうだんしえん",
                 "WADEWADE訪問看護ステーションつくば"]
    
    ##### 月選択 #####
    if form_month.validate_on_submit():
        if request.form.get('workday_name'):
            workday_data_list = request.form.get('workday_name').split('-')
            session["workday_data"] = request.form.get('workday_name') 
            session["y"] = int(workday_data_list[0])
            session["m"] = int(workday_data_list[1])
            
            
            
            
        return redirect(url_for('users_detail', STAFFID=STAFFID))
            
    return render_template('admin/users_detail.html/<STAFFID>', title='ホーム', u=u, typ=typ, form_month=form_month, form=form,
                           tbl_clm=tbl_clm, specification=specification, session=session, STAFFID=STAFFID, team_name=team_name,
                           stf_login= stf_login)
