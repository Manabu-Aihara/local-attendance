from app import routes_attendance_option, jimu_oncall_count
from flask import render_template, flash, redirect, request, session
from werkzeug.urls import url_parse
from flask.helpers import url_for
from flask_login.utils import login_required
from app import app, db
from app.forms import LoginForm, AdminUserCreateForm, ResetPasswordForm, DelForm, UpdateForm, SaveForm, SelectMonthForm
from flask_login import current_user, login_user
from app.models import User, Shinsei, StaffLoggin, Todokede, RecordPaidHoliday, CountAttendance, TimeAttendance
from flask_login import logout_user
from flask import abort
from functools import wraps
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta, date, time
from decimal import Decimal, ROUND_HALF_UP
import jpholiday
import os
from dateutil.relativedelta import relativedelta
from monthdelta import monthmod
from app.attendance_classes import AttendanceAnalysys
from app.calender_classes import MakeCalender
from app.calc_work_classes import DataForTable, CalcTimeClass, PartCalcHolidayTimeClass, get_last_date


os.environ.get('SECRET_KEY') or 'you-will-never-guess'
app.permanent_session_lifetime = timedelta(minutes=360)


"""***** 打刻ページ *****"""

@ app.route('/indextime/<STAFFID>', methods=['GET', 'POST'])
@ login_required
def indextime(STAFFID):
    if app.permanent_session_lifetime == 0:
        return redirect(url_for('logout_mes'))
    
    
    shinseis = Shinsei.query.filter_by(STAFFID=STAFFID).all()
    shin = Shinsei.query.filter_by(STAFFID=STAFFID)
    u = User.query.get(STAFFID)
    rp_holiday = RecordPaidHoliday.query.get(STAFFID)
    cnt_attemdance = CountAttendance.query.get(STAFFID)
    tm_attendance = TimeAttendance.query.get(STAFFID)
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    
    ##### index表示関連 #####
    form_month = SelectMonthForm()
    form = SaveForm()

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
        
    ##### M_NOTIFICATIONとindexの紐づけ #####
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
    dsp_page = ""
    
    if "y" in session:
        workday_data = session["workday_data"]
        y = session["y"]
        m = session["m"]

        if datetime.today().month > 2:
            if datetime.today().year > int(session["y"]) or (datetime.today().year == int(session["y"]) and 
                                                             datetime.today().month > int(session["m"]) + 1):
                #dsp_page = "pointer-events: none;"
                dsp_page = ""
        elif datetime.today().month == 1:
            if datetime.today().year > int(session["y"]) or (datetime.today().year - 1 == int(session["y"]) and int(session["m"]) <= 11):
                #dsp_page = "pointer-events: none;"
                dsp_page = ""
        else:
            if datetime.today().year > int(session["y"]):
                #dsp_page = "pointer-events: none;"
                dsp_page = ""
        
    else:
        workday_data = datetime.today().strftime('%Y-%m-%d')
        y = datetime.now().year
        m = datetime.now().month
        
    

    ##### カレンダーの設定 #####
    cal = []
    hld = []
    
    mkc = MakeCalender(cal, hld, y, m)
    mkc.mkcal()

    shinseis = Shinsei.query.filter(Shinsei.STAFFID == STAFFID).all()

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
    jobtype = u.JOBTYPE_CODE # この職員の職種
    
    users = User.query.all()
    
    #for user in users:
    n = STAFFID
    FromDay = datetime(y, m, 26)  - relativedelta(months=1)
    ToDay = datetime(y, m, 25)
    shins = Shinsei.query.filter(Shinsei.STAFFID==STAFFID, Shinsei.WORKDAY>=FromDay, Shinsei.WORKDAY<=ToDay).all()
    
    if shins:
        
        for shin in shins:

            ##### ２６日基準 カウント
            d = get_last_date(y, m)
                            
            FromDay = datetime(y, m, 26)  - relativedelta(months=1)
            ToDay = datetime(y, m, 25)
            
            base_day = datetime.strptime(shin.WORKDAY, '%Y-%m-%d')
            if ToDay >= base_day and FromDay <= base_day:
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
    ##### 保存ボタン押下処理（１日始まり） 打刻ページ表示で使用 #####
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
            atd = AttendanceAnalysys(c, data0, data1, data2, data3, data_4, data5, data6, data7, data8, data9, data10, data11, STAFFID)            
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

        # パート以外の場合
      
            

        ##### 年間月別勤務時間・日数関係　パート ###############            
        shinseis = Shinsei.query.filter_by(STAFFID=STAFFID).all()
        u = User.query.get(STAFFID)
        rp_holiday = RecordPaidHoliday.query.get(STAFFID)
        tm_attendance = TimeAttendance.query.get(STAFFID)
        cnt_attemdance = CountAttendance.query.get(STAFFID)
            
           
                        

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


    return render_template('attendance/index.html', title='ホーム', cal=cal, shinseis=shinseis, y=y, m=m, form=form, form_month=form_month,
                           oc=oc, oc_cnt=oc_cnt, eg=eg, sk=sk, othr=othr, hld=hld, u=u, bk=bk, tbl_clm=tbl_clm, typ=typ, ptn=ptn,
                           specification=specification, wk=wk, td1=td1, td2=td2, td3=td3, td4=td4, td5=td5, td6=td6, td7=td7,
                           td8=td8, td9=td9, td10=td10, td11=td11, td12=td12, td13=td13, td14=td14, td15=td15, td16=td16,
                           workday_data=workday_data, rp_holiday=rp_holiday, cnt_attemdance=cnt_attemdance, reload_y=reload_y,
                           td17=td17, td18=td18, td19=td19, td20=td20, stf_login=stf_login, length_oncall=length_oncall, team=team,
                           jobtype=jobtype, team_name=team_name, length_oncall_1=length_oncall_1, length_oncall_2=length_oncall_2,
                           length_oncall_3=length_oncall_3, length_oncall_4=length_oncall_4, length_oncall_5=length_oncall_5,
                           length_oncall_6=length_oncall_6, length_oncall_7=length_oncall_7, length_oncall_8=length_oncall_8,
                           dsp_page=dsp_page, STAFFID=STAFFID)
