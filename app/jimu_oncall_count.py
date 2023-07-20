import os
from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal
from functools import wraps

import jpholiday
from dateutil.relativedelta import relativedelta
from flask import abort, flash, redirect, render_template, request, session
from flask.helpers import url_for
from flask_login import current_user, login_user, logout_user
from flask_login.utils import login_required
from monthdelta import monthmod
from werkzeug.security import generate_password_hash
from werkzeug.urls import url_parse

from app import app, db, jimu_every_attendance, routes_attendance_option
from app.attendance_admin_classes import AttendanceAdminAnalysys
from app.calc_work_classes import (CalcTimeClass,
                                   DataForTable,
                                   PartCalcHolidayTimeClass,
                                   TimeOffClass, get_last_date)
from app.calender_classes import MakeCalender
from app.forms import (AdminUserCreateForm, DelForm, EditForm, LoginForm,
                       ResetPasswordForm, SaveForm, SelectMonthForm,
                       UpdateForm)
from app.models import (CountAttendance, CounterForTable, RecordPaidHoliday,
                        Shinsei, StaffLoggin, TimeAttendance, Todokede, User, is_integer_num)

os.environ.get('SECRET_KEY') or 'you-will-never-guess'
app.permanent_session_lifetime = timedelta(minutes=360)


"""######################################## 特別ページの最初の画面 ################################################"""
@app.route('/jimu_select_page', methods=['GET', 'POST'])
@login_required
def jimu_select_page():
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    STAFFID = current_user.STAFFID
    typ = ["submit", "text", "time", "checkbox", "number", "month"]
    select_page = ["オンコールチェック", "所属スタッフ出退勤確認", "常勤スタッフ一覧（１日～末）", 
                   "パートスタッフ一覧（１日～末）", "常勤スタッフ一覧（２６日～２５日）", "パートスタッフ一覧（２６日～２５日）"]
    dat = ["0", "1", "2", "3", "4", "5"]
    
    if request.method == "POST":
        dat = request.form.get('select_page')
        if dat == "":
            return redirect(url_for('jimu_select_page', STAFFID=STAFFID))
        elif dat == "0":
            return redirect(url_for('jimu_oncall_count_26', STAFFID=STAFFID))
        elif dat == "1":
            return redirect(url_for('jimu_users_list', STAFFID=STAFFID))
        elif dat == "2":
            return redirect(url_for('jimu_summary_fulltime', startday=1)) 
        elif dat == "3":
            return redirect(url_for('jimu_summary_fulltime', startday=1)) 
        elif dat == "4":  
            return redirect(url_for('jimu_summary_fulltime', startday=26)) 
        elif dat == "5":
            return redirect(url_for('jimu_summary_fulltime', startday=26)) 
        
            
    return render_template('attendance/jimu_select_page.html', STAFFID=STAFFID, typ=typ, select_page=select_page,
                           dat=dat, stf_login=stf_login)

##### 常勤２６日基準 #####
@app.route('/jimu_oncall_count_26/<STAFFID>', methods=['GET', 'POST'])
@login_required
def jimu_oncall_count_26(STAFFID):
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    typ = ["submit", "text", "time", "checkbox", "number", "month"]
    dat = ["1", "2", "3", "4", "5", "6", "7"]

    form_month = SelectMonthForm()
    
    bumon = ["本社", "宇介", "下介", "鹿介", "KO介", "宇福", "KO福", "鹿福", "筑波介"]
    syozoku = ["本社", "宇都宮", "下野", "鹿沼", "KODOMOTO", "在宅支援", "KOそうだん", "つくば"]
    syokusyu = ["NS", "事務", "OT", "ST", "PT",
                "相談専門", "相談補助", "保育支援", "准NS", "開発", "広報"]
    keitai = ["8H", "パート", "6H", "7H", "32H"]

    team = ""

    dwl_today = datetime.today()
    
    staffid = STAFFID
    jimu_usr = User.query.get(staffid)
    
    users = User.query.all()
    cfts = CounterForTable.query.all()

    if form_month.validate_on_submit():
        
        session["select_data"] = request.form.get('select_team')
        select_data = session["select_data"]
        
        if select_data == "1":
            team = "2"
        elif select_data == "2":
            team = "3"
        elif select_data == "3":
            team = "4"
        elif select_data == "4":
            team = "5"
        elif select_data == "5":
            team = "6"
        elif select_data == "6":
            team = "7"    
        elif select_data == "7":
            team = "8"
     
        
        selected_workday = request.form.get('workday_nm')
        
        if selected_workday:
            y = datetime.strptime(selected_workday, '%Y-%m').year
            m = datetime.strptime(selected_workday, '%Y-%m').month
        else:
            y = datetime.today().year
            m = datetime.today().month


        session['workday_dat'] = selected_workday
        workday_dat = session['workday_dat']

        onc_2 = []
        onc_3 = []
        onc_4 = []
        onc_5 = []
        onc_6 = []
        onc_7 = []
        onc_8 = []
        
        onchol_2 = []
        onchol_3 = []
        onchol_4 = []
        onchol_5 = []
        onchol_6 = []
        onchol_7 = []
        onchol_8 = []
       
        oncnum_2 = 0
        oncnum_3 = 0
        oncnum_4 = 0
        oncnum_5 = 0
        oncnum_6 = 0
        oncnum_7 = 0
        oncnum_8 = 0
        
        angelnum_2 = 0
        angelnum_3 = 0
        angelnum_4 = 0
        angelnum_5 = 0
        angelnum_6 = 0
        angelnum_7 = 0
        angelnum_8 = 0                   

        for user in users:  ############### 
            n = user.STAFFID
            shins = Shinsei.query.filter(Shinsei.STAFFID==n).all()
            cnt_for_tbl = CounterForTable.query.get(n)
            
            
            onc = []            
            onchol = []
            oncnum = 0             
            angelnum = 0            
                        
            if shins:                
                for shin in shins:
                    d = get_last_date(y, m)
                    ##### ２６日基準 カウント
                    FromDay = datetime(y, m, 26)  - relativedelta(months=1)
                    ToDay = datetime(y, m, 25)
                    base_day = datetime.strptime(shin.WORKDAY, '%Y-%m-%d')
                    if (ToDay >= base_day) and (FromDay <= base_day):

                        if shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 2:
                            onc.append("cnt_02")
                            onc_2.append("cnt_2")
                            oncnum += int(shin.ONCALL_COUNT)
                            oncnum_2 += int(shin.ONCALL_COUNT)
                            angelnum += int(shin.ENGEL_COUNT)
                            angelnum_2 += int(shin.ENGEL_COUNT)
                            if shin.HOLIDAY == "1":
                                onchol.append("hol_02")
                                onchol_2.append("hol_2") 
                            
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 3:
                            onc.append("cnt_03")
                            onc_3.append("cnt_3")
                            oncnum += int(shin.ONCALL_COUNT)
                            oncnum_3 += int(shin.ONCALL_COUNT)
                            angelnum += int(shin.ENGEL_COUNT)
                            angelnum_3 += int(shin.ENGEL_COUNT)
                            if shin.HOLIDAY == "1":
                                onchol.append("hol_03")
                                onchol_3.append("hol_3") 
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 4:
                            onc.append("cnt_04")
                            onc_4.append("cnt_4")
                            oncnum += int(shin.ONCALL_COUNT)
                            oncnum_4 += int(shin.ONCALL_COUNT)
                            angelnum += int(shin.ENGEL_COUNT)
                            angelnum_4 += int(shin.ENGEL_COUNT)
                            if shin.HOLIDAY == "1":
                                onchol.append("hol_04")
                                onchol_4.append("hol_4") 
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 5:
                            onc.append("cnt_05")
                            onc_5.append("cnt_5")
                            oncnum += int(shin.ONCALL_COUNT)
                            oncnum_5 += int(shin.ONCALL_COUNT)
                            angelnum += int(shin.ENGEL_COUNT)
                            angelnum_5 += int(shin.ENGEL_COUNT)
                            if shin.HOLIDAY == "1":
                                onchol.append("hol_05")
                                onchol_5.append("hol_5") 
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 6:
                            onc.append("cnt_06")
                            onc_6.append("cnt_6")
                            oncnum += int(shin.ONCALL_COUNT)
                            oncnum_6 += int(shin.ONCALL_COUNT)
                            angelnum += int(shin.ENGEL_COUNT)
                            angelnum_6 += int(shin.ENGEL_COUNT)
                            if shin.HOLIDAY == "1":
                                onchol.append("hol_06")
                                onchol_2.append("hol_6") 
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 7:
                            onc.append("cnt_07")
                            onc_7.append("cnt_7")
                            oncnum += int(shin.ONCALL_COUNT)
                            oncnum_7 += int(shin.ONCALL_COUNT)
                            angelnum += int(shin.ENGEL_COUNT)
                            angelnum_7 += int(shin.ENGEL_COUNT)
                            if shin.HOLIDAY == "1":
                                onchol.append("hol_07")
                                onchol_7.append("hol_7") 
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 8:
                            onc.append("cnt_08")
                            onc_8.append("cnt_8")
                            oncnum += int(shin.ONCALL_COUNT)
                            oncnum_8 += int(shin.ONCALL_COUNT)
                            angelnum += int(shin.ENGEL_COUNT)
                            angelnum_8 += int(shin.ENGEL_COUNT)
                            if shin.HOLIDAY == "1":
                                onchol.append("hol_08")
                                onchol_8.append("hol_8")                              
                                
                     


            if cnt_for_tbl:
                cnt_for_tbl.ONCALL = len(onc) - len(onchol)
                cnt_for_tbl.ONCALL_HOLIDAY = len(onchol)
                cnt_for_tbl.ONCALL_COUNT = oncnum
                cnt_for_tbl.ENGEL_COUNT = angelnum
                            
                db.session.commit()


        length_oncall_2 = len(onc_2) - len(onchol_2)
        length_oncall_3 = len(onc_3) - len(onchol_3)                               
        length_oncall_4 = len(onc_4) - len(onchol_4)
        length_oncall_5 = len(onc_5) - len(onchol_5)   
        length_oncall_6 = len(onc_6) - len(onchol_6)   
        length_oncall_7 = len(onc_7) - len(onchol_7)
        length_oncall_8 = len(onc_8) - len(onchol_8)
        
        length_onchol_2 = len(onchol_2) 
        length_onchol_3 = len(onchol_3)
        length_onchol_4 = len(onchol_4)
        length_onchol_5 = len(onchol_5)
        length_onchol_6 = len(onchol_6)
        length_onchol_7 = len(onchol_7)
        length_onchol_8 = len(onchol_8)
        
        length_oncnum_2 = oncnum_2
        length_oncnum_3 = oncnum_3
        length_oncnum_4 = oncnum_4
        length_oncnum_5 = oncnum_5
        length_oncnum_6 = oncnum_6
        length_oncnum_7 = oncnum_7
        length_oncnum_8 = oncnum_8
        
        length_angelnum_2 = angelnum_2
        length_angelnum_3 = angelnum_3
        length_angelnum_4 = angelnum_4
        length_angelnum_5 = angelnum_5
        length_angelnum_6 = angelnum_6
        length_angelnum_7 = angelnum_7
        length_angelnum_8 = angelnum_8        
        
        length_oncall = length_oncall_2 + length_oncall_3 + length_oncall_4 + length_oncall_5 + length_oncall_6 + length_oncall_7 + length_oncall_8
        length_onchol = length_onchol_2 + length_onchol_3 + length_onchol_4 + length_onchol_5 + length_onchol_6 + length_onchol_7 + length_onchol_8
        length_oncnum = length_oncnum_2 + length_oncnum_3 + length_oncnum_4 + length_oncnum_5 + length_oncnum_6 + length_oncnum_7 + length_oncnum_8
        length_angelnum = length_angelnum_2 + length_angelnum_3 + length_angelnum_4 + length_angelnum_5 + length_angelnum_6 + length_angelnum_7 + length_angelnum_8
             

    else:
        y = datetime.today().year
        m = datetime.today().month
        
        workday_dat = str(y) + "-" + str(m)
        
        team = ""

        onc_2 = []
        onc_3 = []
        onc_4 = []
        onc_5 = []
        onc_6 = []
        onc_7 = []
        onc_8 = []
        
        onchol_2 = []
        onchol_3 = []
        onchol_4 = []
        onchol_5 = []
        onchol_6 = []
        onchol_7 = []
        onchol_8 = []
       
        oncnum_2 = 0
        oncnum_3 = 0
        oncnum_4 = 0
        oncnum_5 = 0
        oncnum_6 = 0
        oncnum_7 = 0
        oncnum_8 = 0
        
        angelnum_2 = 0
        angelnum_3 = 0
        angelnum_4 = 0
        angelnum_5 = 0
        angelnum_6 = 0
        angelnum_7 = 0
        angelnum_8 = 0  
        
        users = User.query.all()                 

        for user in users:  ############### 
            n = user.STAFFID
            shins = Shinsei.query.filter(Shinsei.STAFFID==n).all()
            cnt_for_tbl = CounterForTable.query.get(n)
            
            onc = []            
            onchol = []
            oncnum = 0             
            angelnum = 0            
                        
            if shins:                
                for shin in shins:

                    d = get_last_date(y, m)
                    ##### ２６日基準 カウント
                    FromDay = datetime(y, m, 26)  - relativedelta(months=1)
                    ToDay = datetime(y, m, 25)
                   
                    base_day = datetime.strptime(shin.WORKDAY, '%Y-%m-%d')
                    if (ToDay >= base_day) and (FromDay < base_day):

                        if shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 2:
                            onc.append("cnt_02")
                            onc_2.append("cnt_2")
                            oncnum += int(shin.ONCALL_COUNT)
                            oncnum_2 += int(shin.ONCALL_COUNT)
                            angelnum += int(shin.ENGEL_COUNT)
                            angelnum_2 += int(shin.ENGEL_COUNT)
                            if shin.HOLIDAY == "1":
                                onchol.append("hol_02")
                                onchol_2.append("hol_2") 
                            
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 3:
                            onc.append("cnt_03")
                            onc_3.append("cnt_3")
                            oncnum += int(shin.ONCALL_COUNT)
                            oncnum_3 += int(shin.ONCALL_COUNT)
                            angelnum += int(shin.ENGEL_COUNT)
                            angelnum_3 += int(shin.ENGEL_COUNT)
                            if shin.HOLIDAY == "1":
                                onchol.append("hol_03")
                                onchol_3.append("hol_3")
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 4:
                            onc.append("cnt_04")
                            onc_4.append("cnt_4")
                            oncnum += int(shin.ONCALL_COUNT)
                            oncnum_4 += int(shin.ONCALL_COUNT)
                            angelnum += int(shin.ENGEL_COUNT)
                            angelnum_4 += int(shin.ENGEL_COUNT)
                            if shin.HOLIDAY == "1":
                                onchol.append("hol_04")
                                onchol_4.append("hol_4") 
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 5:
                            onc.append("cnt_05")
                            onc_5.append("cnt_5")
                            oncnum += int(shin.ONCALL_COUNT)
                            oncnum_5 += int(shin.ONCALL_COUNT)
                            angelnum += int(shin.ENGEL_COUNT)
                            angelnum_5 += int(shin.ENGEL_COUNT)
                            if shin.HOLIDAY == "1":
                                onchol.append("hol_05")
                                onchol_5.append("hol_5") 
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 6:
                            onc.append("cnt_06")
                            onc_6.append("cnt_6")
                            oncnum += int(shin.ONCALL_COUNT)
                            oncnum_6 += int(shin.ONCALL_COUNT)
                            angelnum += int(shin.ENGEL_COUNT)
                            angelnum_6 += int(shin.ENGEL_COUNT)
                            if shin.HOLIDAY == "1":
                                onchol.append("hol_06")
                                onchol_2.append("hol_6") 
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 7:
                            onc.append("cnt_07")
                            onc_7.append("cnt_7")
                            oncnum += int(shin.ONCALL_COUNT)
                            oncnum_7 += int(shin.ONCALL_COUNT)
                            angelnum += int(shin.ENGEL_COUNT)
                            angelnum_7 += int(shin.ENGEL_COUNT)
                            if shin.HOLIDAY == "1":
                                onchol.append("hol_07")
                                onchol_7.append("hol_7") 
                        elif shin.ONCALL == "1" and User.query.get(n).TEAM_CODE == 8:
                            onc.append("cnt_08")
                            onc_8.append("cnt_8")
                            oncnum += int(shin.ONCALL_COUNT)
                            oncnum_8 += int(shin.ONCALL_COUNT)
                            angelnum += int(shin.ENGEL_COUNT)
                            angelnum_8 += int(shin.ENGEL_COUNT)
                            if shin.HOLIDAY == "1":
                                onchol.append("hol_08")
                                onchol_8.append("hol_8")                              
                                
                    


            if cnt_for_tbl:
                cnt_for_tbl.ONCALL = len(onc) - len(onchol)
                cnt_for_tbl.ONCALL_HOLIDAY = len(onchol)
                cnt_for_tbl.ONCALL_COUNT = oncnum
                cnt_for_tbl.ENGEL_COUNT = angelnum
                            
                db.session.commit()


        length_oncall_2 = len(onc_2) - len(onchol_2)
        length_oncall_3 = len(onc_3) - len(onchol_3)                               
        length_oncall_4 = len(onc_4) - len(onchol_4)
        length_oncall_5 = len(onc_5) - len(onchol_5)   
        length_oncall_6 = len(onc_6) - len(onchol_6)   
        length_oncall_7 = len(onc_7) - len(onchol_7)
        length_oncall_8 = len(onc_8) - len(onchol_8)
        
        length_onchol_2 = len(onchol_2) 
        length_onchol_3 = len(onchol_3)
        length_onchol_4 = len(onchol_4)
        length_onchol_5 = len(onchol_5)
        length_onchol_6 = len(onchol_6)
        length_onchol_7 = len(onchol_7)
        length_onchol_8 = len(onchol_8)
        
        length_oncnum_2 = oncnum_2
        length_oncnum_3 = oncnum_3
        length_oncnum_4 = oncnum_4
        length_oncnum_5 = oncnum_5
        length_oncnum_6 = oncnum_6
        length_oncnum_7 = oncnum_7
        length_oncnum_8 = oncnum_8
        
        length_angelnum_2 = angelnum_2
        length_angelnum_3 = angelnum_3
        length_angelnum_4 = angelnum_4
        length_angelnum_5 = angelnum_5
        length_angelnum_6 = angelnum_6
        length_angelnum_7 = angelnum_7
        length_angelnum_8 = angelnum_8        
        
        length_oncall = length_oncall_2 + length_oncall_3 + length_oncall_4 + length_oncall_5 + length_oncall_6 + length_oncall_7 + length_oncall_8
        length_onchol = length_onchol_2 + length_onchol_3 + length_onchol_4 + length_onchol_5 + length_onchol_6 + length_onchol_7 + length_onchol_8
        length_oncnum = length_oncnum_2 + length_oncnum_3 + length_oncnum_4 + length_oncnum_5 + length_oncnum_6 + length_oncnum_7 + length_oncnum_8
        length_angelnum = length_angelnum_2 + length_angelnum_3 + length_angelnum_4 + length_angelnum_5 + length_angelnum_6 + length_angelnum_7 + length_angelnum_8


        

    return render_template('attendance/jimu_oncall_count_26.html', typ=typ, form_month=form_month, workday_dat=workday_dat, y=y, m=m, dwl_today=dwl_today,
                           users=users, cfts=cfts, bumon=bumon, syozoku=syozoku, syokusyu=syokusyu, keitai=keitai, 
                           jimu_usr=jimu_usr, STAFFID=staffid, length_oncall=length_oncall, length_oncall_2=length_oncall_2, length_oncall_3=length_oncall_3,
                           length_oncall_4=length_oncall_4, length_oncall_5=length_oncall_5, length_oncall_6=length_oncall_6, length_oncall_7=length_oncall_7,
                           length_oncall_8=length_oncall_8, length_onchol_2=length_onchol_2, length_onchol_3=length_onchol_3, length_onchol_4=length_onchol_4,
                           length_onchol_5=length_onchol_5, length_onchol_6=length_onchol_6, length_onchol_7=length_onchol_7, length_onchol_8=length_onchol_8,
                           length_oncnum_2=length_oncnum_2, length_oncnum_3=length_oncnum_3, length_oncnum_4=length_oncnum_4, length_oncnum_5=length_oncnum_5,
                           length_oncnum_6=length_oncnum_6, length_oncnum_7=length_oncnum_7, length_oncnum_8=length_oncnum_8,
                           length_angelnum_2=length_angelnum_2, length_angelnum_3=length_angelnum_3, length_angelnum_4=length_angelnum_4,
                           length_angelnum_5=length_angelnum_5, length_angelnum_6=length_angelnum_6, length_angelnum_7=length_angelnum_7,
                           length_angelnum_8=length_angelnum_8, length_onchol=length_onchol, length_oncnum=length_oncnum,
                           length_angelnum=length_angelnum, dat=dat, team=team, stf_login=stf_login)

##### 常勤1日基準 ######
@app.route('/jimu_summary_fulltime/<startday>', methods=['GET', 'POST'])
@login_required
def jimu_summary_fulltime(startday):
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    typ = ["submit", "text", "time", "checkbox", "number", "date"]
    form_month = SelectMonthForm()
    workday_data = ""
    str_workday = "月選択をしてください。"
    bumon = ["本社", "宇介", "下介", "鹿介", "KO介", "宇福", "KO福", "鹿福", "筑波介"]
    syozoku = ["本社", "宇都宮", "下野", "鹿沼", "KODOMOTO", "在宅支援", "KOそうだん", "つくば"]
    syokusyu = ["NS", "事務", "OT", "ST", "PT",
                "相談専門", "相談補助", "保育支援", "准NS", "開発", "広報"]
    keitai = ["8H", "パート", "6H", "7H", "32H"]
    y = ""
    m = ""
    outer_display = 0
    
    dwl_today = datetime.today()

    users = User.query.all()
    cfts = CounterForTable.query.all()
    
    jimu_usr =User.query.get(current_user.STAFFID)

    # 年月選択をしたかどうか
    if form_month.validate_on_submit():
        selected_workday = request.form.get('workday_name') ##### 選択された日付

        if selected_workday:
            y = datetime.strptime(selected_workday, '%Y-%m').year
            m = datetime.strptime(selected_workday, '%Y-%m').month
        else:
            y = datetime.today().year
            m = datetime.today().month

        #session['workday_data'] = selected_workday
        #workday_data = session['workday_data']
    else:
        y = datetime.today().year
        m = datetime.today().month
        #workday_data = datetime.today().strftime('%Y-%m-%d')

    for user in users:
        staffid = user.STAFFID 
        shinseis = Shinsei.query.filter_by(STAFFID=staffid).all()
        u = User.query.get(staffid)
        cnt_for_tbl = CounterForTable.query.get(staffid)
        rp_holiday = RecordPaidHoliday.query.get(staffid)
                      
        
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

        real_time = []
        real_time_sum = []
        syukkin_times_0 = []
        syukkin_holiday_times_0 = []
        over_time_0 = []
        
        timeoff1 = []
        timeoff2 = []
        timeoff3 = []
        halfway_through1 = []
        halfway_through2 = []
        halfway_through3 = []   

        for sh in shinseis:

            

            #if u.CONTRACT_CODE == 2:
            ##### １日基準 #####

            d = get_last_date(y, m)
            if int(startday) != 1:
                #1日開始以外の場合
                FromDay = datetime(y, m, int(startday))  - relativedelta(months=1)
                ToDay = datetime(y, m, 25)
            else:
                #1日開始の場合
                FromDay = datetime(y, m, int(startday))
                ToDay = datetime(y, m, d)
            
            dft = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half, tikoku, soutai, kekkin,
                                syuttyou, syuttyou_half, reflesh, s_kyori, FromDay, ToDay)
            dft.other_data()

            tm_off = TimeOffClass(y, m, d, sh.WORKDAY, sh.NOTIFICATION, sh.NOTIFICATION2, timeoff1, timeoff2, timeoff3,
                                halfway_through1, halfway_through2, halfway_through3)
            tm_off.cnt_time_off()

           

            

            if FromDay <= datetime.strptime(sh.WORKDAY, '%Y-%m-%d') and ToDay >= datetime.strptime(sh.WORKDAY, '%Y-%m-%d'):
                dtm = datetime.strptime(sh.ENDTIME, '%H:%M') - datetime.strptime(sh.STARTTIME, '%H:%M')
                #リアル実働時間
                real_time = dtm
                

                settime = CalcTimeClass(dtm, sh.NOTIFICATION, sh.NOTIFICATION2, sh.STARTTIME, sh.ENDTIME, sh.OVERTIME,
                                        u.CONTRACT_CODE, syukkin_times_0, over_time_0, rp_holiday.BASETIMES_PAIDHOLIDAY, 
                                         real_time, real_time_sum, syukkin_holiday_times_0, sh.HOLIDAY, u.JOBTYPE_CODE, staffid, sh.WORKDAY)
                settime.calc_time()
           

        ##### データベース貯蔵 #####
        ln_oncall = len(oncall)
        ln_oncall_holiday = len(oncall_holiday)
        
        ln_oncall_cnt = 0
        for oc in oncall_cnt:
            if str.isnumeric(oc):
                ln_oncall_cnt += int(oc)
                        
        ln_engel_cnt= 0
        for ac in engel_cnt:
            if str.isnumeric(ac):
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
            if is_integer_num(s):
                ln_s_kyori += float(s)

        sum_0 = 0
        real_sum = 0
        for n in range(len(syukkin_times_0)):
            if is_integer_num(syukkin_times_0[n]):
                sum_0 += syukkin_times_0[n]

        w_h = sum_0 // (60 * 60)
        w_m = (sum_0 - w_h * 60 * 60) // 60
        working_time = w_h + w_m / 100
        working_time_10 = sum_0 / (60 * 60)

        for n in range(len(real_time_sum)):
            real_sum += real_time_sum[n]
        w_h = real_sum // (60 * 60)
        w_m = (real_sum - w_h * 60 * 60) // 60
        real_time = w_h + w_m / 100
        real_time_10 = real_sum / (60 * 60)      

        sum_over_0 = 0
        for n in range(len(over_time_0)):
            if not over_time_0[n]:
                sum_over_0 = sum_over_0
            else:
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
        
        sum_timeoff1 = len(timeoff1)
        sum_timeoff2 = len(timeoff2)
        sum_timeoff3 = len(timeoff3)
        timeoff = sum_timeoff1 + sum_timeoff2 * 2 + sum_timeoff3 * 3
        
        sum_halfway_through1 = len(halfway_through1)
        sum_halfway_through2 = len(halfway_through2)
        sum_halfway_through3 = len(halfway_through3)
        halfway_through = sum_halfway_through1 + sum_halfway_through2 * 2 + sum_halfway_through3 * 3


        if cnt_for_tbl:
            cnt_for_tbl.ONCALL = ln_oncall
            cnt_for_tbl.ONCALL_HOLIDAY = ln_oncall_holiday
            cnt_for_tbl.ONCALL_COUNT = ln_oncall_cnt
            cnt_for_tbl.ENGEL_COUNT = ln_engel_cnt
            cnt_for_tbl.NENKYU = ln_nenkyu
            cnt_for_tbl.NENKYU_HALF = ln_nenkyu_half
            cnt_for_tbl.TIKOKU = ln_tikoku
            cnt_for_tbl.SOUTAI = ln_soutai
            cnt_for_tbl.KEKKIN = ln_kekkin
            cnt_for_tbl.SYUTTYOU = ln_syuttyou
            cnt_for_tbl.SYUTTYOU_HALF = ln_syuttyou_half
            cnt_for_tbl.REFLESH = ln_reflesh
            cnt_for_tbl.MILEAGE = ln_s_kyori
            cnt_for_tbl.SUM_WORKTIME = working_time
            cnt_for_tbl.SUM_REAL_WORKTIME = real_time
            cnt_for_tbl.OVERTIME = over
            cnt_for_tbl.HOLIDAY_WORK = holiday_work
            cnt_for_tbl.WORKDAY_COUNT = workday_count
            cnt_for_tbl.SUM_WORKTIME_10 = working_time_10
            cnt_for_tbl.OVERTIME_10= over_10
            cnt_for_tbl.HOLIDAY_WORK_10 = holiday_work_10
            cnt_for_tbl.TIMEOFF = timeoff
            cnt_for_tbl.HALFWAY_THROUGH = halfway_through

            db.session.commit()
                
            ##### 退職者表示設定
              

    return render_template('attendance/jimu_summary_fulltime.html', startday=startday, typ=typ, form_month=form_month, workday_data=workday_data, y=y, m=m, dwl_today=dwl_today,
                           users=users, cfts=cfts, str_workday=str_workday, bumon=bumon, syozoku=syozoku, syokusyu=syokusyu, 
                           keitai=keitai, jimu_usr=jimu_usr, stf_login=stf_login, workday_count=workday_count,
                           timeoff=timeoff, halfway_rough=halfway_through, FromDay=FromDay.date(), ToDay=ToDay.date())

   

@app.route('/jimu_users_list/<STAFFID>', methods=['GET', 'POST'])
@login_required
def jimu_users_list(STAFFID):
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    jimu_usr = User.query.get(STAFFID)
    usrs = User.query.filter_by(TEAM_CODE=jimu_usr.TEAM_CODE).all()
    us = User.query.all()
    
    return render_template('attendance/jimu_users_list.html', jimu_usr=jimu_usr, usrs=usrs, us=us, stf_login=stf_login)





@ app.route('/jimu_users_select/<STAFFID>', methods=['GET', 'POST'])
@ login_required
def jimu_users_select(STAFFID):
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    shinseis = Shinsei.query.filter_by(STAFFID=STAFFID).all()
    STAFFID = STAFFID
    shin = Shinsei.query.filter_by(STAFFID=STAFFID)
    u = User.query.get(STAFFID)
            
    ##### index表示関連 #####
    form_month = SelectMonthForm()
    form = SaveForm()
    
    tbl_clm = ["日付", "曜日", "oncall", "oncall対応件数", "engel対応件数",
               "開始時間", "終了時間", "走行距離", "届出（午前）", "残業申請", "備考", "届出（午後）"]
    wk = ["日", "土", "月", "火", "水", "木", "金"]
    ptn = ["^[0-9０-９]+$", "^[0-9.０-９．]+$"]
    specification = ["readonly", "checked", "selected", "hidden"]
    typ = ["submit", "text", "time", "checkbox", "number", "date"]
    
    ##### 月選択 #####
    if form_month.validate_on_submit():
        if request.form.get('workday_name'):
            workday_data_list = request.form.get('workday_name').split('-')
            session["workday_data"] = request.form.get('workday_name') 
            session["y"] = int(workday_data_list[0])
            session["m"] = int(workday_data_list[1])
            
            
            
            
        return redirect(url_for('jimu_users_attendance_edit', STAFFID=STAFFID))
            
    return render_template('attendance/jimu_edit_users_attendance.html', title='ホーム', u=u, typ=typ, form_month=form_month, form=form,
                           tbl_clm=tbl_clm, specification=specification, session=session, stf_login=stf_login)    
    
    
    


##### パート２６日基準 #####


@app.route('/jimu_summary_parttime26', methods=['GET', 'POST'])
@login_required
def jimu_summary_parttime26():
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    typ = ["submit", "text", "time", "checkbox", "number", "date"]
    form_month = SelectMonthForm()

    workday_data = ""
    str_workday = "月選択をしてください"
    str_workday = "月選択をしてください"
    bumon = ["本社", "宇介", "下介", "鹿介", "KO介", "宇福", "KO福", "鹿福", "筑波介"]
    syozoku = ["本社", "宇都宮", "下野", "鹿沼", "KODOMOTO", "在宅支援", "KOそうだん", "つくば"]
    syokusyu = ["NS", "事務", "OT", "ST", "PT",
                "相談専門", "相談補助", "保育支援", "准NS", "開発", "広報"]
    keitai = ["8H", "パート", "6H", "7H", "32H"]
    y = ""
    m = ""
    outer_display = 0
    
    dwl_today = datetime.today()    

    users = User.query.all()
    cfts = CounterForTable.query.all()
    
    jimu_usr = User.query.get(current_user.STAFFID)

    if form_month.validate_on_submit():
        selected_workday = request.form.get('workday_name')

        if selected_workday:
            y = datetime.strptime(selected_workday, '%Y-%m').year
            m = datetime.strptime(selected_workday, '%Y-%m').month
        else:
            y = datetime.today().year
            m = datetime.today().month

        session['workday_data'] = selected_workday
        workday_data = session['workday_data']

        for user in users:
            staffid = user.STAFFID
            shinseis = Shinsei.query.filter_by(STAFFID=staffid).all()
            u = User.query.get(staffid)
            rp_holiday = RecordPaidHoliday.query.get(staffid)
            tm_attendance = TimeAttendance.query.get(staffid)
            cnt_for_tbl = CounterForTable.query.get(staffid)
            
            

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
            
            timeoff1 = []
            timeoff2 = []
            timeoff3 = []
            halfway_through1 = []
            halfway_through2 = []
            halfway_through3 = []               

            for sh in shinseis:


                if u.CONTRACT_CODE == 2:

                    ##### 月間実働時間（２６日基準） #####
                    if m == 1:  # 1月
                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if (datetime(y, m, 1) >= base_day) and (datetime(y - 1, m + 11, 25) < base_day):
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
                        if (datetime(y, m, 25) >= base_day) and (datetime(y, m - 1, 25) < base_day):
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
                        if (datetime(y, m, 25) >= base_day) and (datetime(y, m - 1, 25) < base_day):                        
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
                        if (datetime(y, m, 25) >= base_day) and (datetime(y, m - 1, 25) < base_day):                        
                        
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
                        if (datetime(y, m, 25) >= base_day) and (datetime(y, m - 1, 25) < base_day):                        
                        
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
                        if (datetime(y, m, 25) >= base_day) and (datetime(y, m - 1, 25) < base_day):                        
                        
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
                        if (datetime(y, m, 25) >= base_day) and (datetime(y, m - 1, 25) < base_day):                        
                        
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
                        if (datetime(y, m, 25) >= base_day) and (datetime(y, m - 1, 25) < base_day):                        
                        
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
                        if (datetime(y, m, 25) >= base_day) and (datetime(y, m - 1, 25) < base_day):                        
                        
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
                        if (datetime(y, m, 25) >= base_day) and (datetime(y, m - 1, 25) < base_day):                        
                        
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
                        if (datetime(y, m, 25) >= base_day) and (datetime(y, m - 1, 25) < base_day):                        
                        
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
                        if (datetime(y, m, 25) >= base_day) and (datetime(y, m - 1, 25) < base_day):                        
                        
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
                        if (datetime(y, m, 1) >= base_day) and (datetime(y - 1, m + 11, 25) < base_day):
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
                                
                            if sh.NOTIFICATION == "10" or sh.NOTIFICATION2 == "10":
                                timeoff1.append(cnt1)
                            if sh.NOTIFICATION == "11" or sh.NOTIFICATION2 == "11":
                                timeoff2.append(cnt2)
                            if sh.NOTIFICATION == "12" or sh.NOTIFICATION2 == "12":
                                timeoff3.append(cnt3)
                            if sh.NOTIFICATION == "13" or sh.NOTIFICATION2 == "13":
                                halfway_through1.append(cnt01)
                            if sh.NOTIFICATION == "14" or sh.NOTIFICATION2 == "14":
                                halfway_through2.append(cnt02)
                            if sh.NOTIFICATION == "15" or sh.NOTIFICATION2 == "15":
                                halfway_through3.append(cnt03)

                    if m == 2:  # ２月
                        if y % 4 == 0:
                            d = 29
                        elif y % 4 != 0:
                            d = 28

                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if (datetime(y, m, 25) >= base_day) and (datetime(y, m - 1, 25) < base_day):
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
                                
                            if sh.NOTIFICATION == "10" or sh.NOTIFICATION2 == "10":
                                timeoff1.append(cnt1)
                            if sh.NOTIFICATION == "11" or sh.NOTIFICATION2 == "11":
                                timeoff2.append(cnt2)
                            if sh.NOTIFICATION == "12" or sh.NOTIFICATION2 == "12":
                                timeoff3.append(cnt3)
                            if sh.NOTIFICATION == "13" or sh.NOTIFICATION2 == "13":
                                halfway_through1.append(cnt01)
                            if sh.NOTIFICATION == "14" or sh.NOTIFICATION2 == "14":
                                halfway_through2.append(cnt02)
                            if sh.NOTIFICATION == "15" or sh.NOTIFICATION2 == "15":
                                halfway_through3.append(cnt03)

                    if m == 3:  # ３月
                        d = 31
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                               sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                               oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                               tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)
                        dft26.other_data26()

                        tm_off = TimeOffClass(y, m, d, sh.WORKDAY, sh.NOTIFICATION, sh.NOTIFICATION2, timeoff1, timeoff2, timeoff3,
                                            halfway_through1, halfway_through2, halfway_through3)
                        tm_off.cnt_time_off()

                    if m == 4:  # ４月
                        d = 30
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                               sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                               oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                               tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                        tm_off = TimeOffClass(y, m, d, sh.WORKDAY, sh.NOTIFICATION, sh.NOTIFICATION2, timeoff1, timeoff2, timeoff3,
                                            halfway_through1, halfway_through2, halfway_through3)
                        tm_off.cnt_time_off()

                    if m == 5:  # ５月
                        d = 31
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                               sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                               oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                               tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                        tm_off = TimeOffClass(y, m, d, sh.WORKDAY, sh.NOTIFICATION, sh.NOTIFICATION2, timeoff1, timeoff2, timeoff3,
                                            halfway_through1, halfway_through2, halfway_through3)
                        tm_off.cnt_time_off()

                    if m == 6:  # ６月
                        d = 30
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                               sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                               oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                               tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                        tm_off = TimeOffClass(y, m, d, sh.WORKDAY, sh.NOTIFICATION, sh.NOTIFICATION2, timeoff1, timeoff2, timeoff3,
                                            halfway_through1, halfway_through2, halfway_through3)
                        tm_off.cnt_time_off()

                    if m == 7:  # ７月
                        d = 31
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                               sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                               oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                               tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                        tm_off = TimeOffClass(y, m, d, sh.WORKDAY, sh.NOTIFICATION, sh.NOTIFICATION2, timeoff1, timeoff2, timeoff3,
                                            halfway_through1, halfway_through2, halfway_through3)
                        tm_off.cnt_time_off()

                    if m == 8:  # ８月
                        d = 31
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                               sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                               oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                               tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                        tm_off = TimeOffClass(y, m, d, sh.WORKDAY, sh.NOTIFICATION, sh.NOTIFICATION2, timeoff1, timeoff2, timeoff3,
                                            halfway_through1, halfway_through2, halfway_through3)
                        tm_off.cnt_time_off()

                    if m == 9:  # ９月
                        d = 30
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                               sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                               oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                               tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                        tm_off = TimeOffClass(y, m, d, sh.WORKDAY, sh.NOTIFICATION, sh.NOTIFICATION2, timeoff1, timeoff2, timeoff3,
                                            halfway_through1, halfway_through2, halfway_through3)
                        tm_off.cnt_time_off()

                    if m == 10:  # １０月
                        d = 31
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                               sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                               oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                               tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                        tm_off = TimeOffClass(y, m, d, sh.WORKDAY, sh.NOTIFICATION, sh.NOTIFICATION2, timeoff1, timeoff2, timeoff3,
                                            halfway_through1, halfway_through2, halfway_through3)
                        tm_off.cnt_time_off()

                    if m == 11:  # １１月
                        d = 30
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                               sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                               oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                               tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                        tm_off = TimeOffClass(y, m, d, sh.WORKDAY, sh.NOTIFICATION, sh.NOTIFICATION2, timeoff1, timeoff2, timeoff3,
                                            halfway_through1, halfway_through2, halfway_through3)
                        tm_off.cnt_time_off()

                    if m == 12:  # １２月
                        d = 31
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                               sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                               oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                               tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                        tm_off = TimeOffClass(y, m, d, sh.WORKDAY, sh.NOTIFICATION, sh.NOTIFICATION2, timeoff1, timeoff2, timeoff3,
                                            halfway_through1, halfway_through2, halfway_through3)
                        tm_off.cnt_time_off()


            ##### データベース貯蔵 #####
            ln_oncall = len(oncall)
            ln_oncall_holiday = len(oncall_holiday)

            ln_oncall_cnt = 0
            for oc in oncall_cnt:
                ln_oncall_cnt += int(oc)
                
            ln_engel_cnt= 0
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
            
            sum_timeoff1 = len(timeoff1)
            sum_timeoff2 = len(timeoff2)
            sum_timeoff3 = len(timeoff3)
            timeoff = sum_timeoff1 + sum_timeoff2 * 2 + sum_timeoff3 * 3
            
            sum_halfway_through1 = len(halfway_through1)
            sum_halfway_through2 = len(halfway_through2)
            sum_halfway_through3 = len(halfway_through3)
            halfway_through = sum_halfway_through1 + sum_halfway_through2 * 2 + sum_halfway_through3 * 3


            if cnt_for_tbl:
                cnt_for_tbl.ONCALL = ln_oncall
                cnt_for_tbl.ONCALL_HOLIDAY = ln_oncall_holiday
                cnt_for_tbl.ONCALL_COUNT = ln_oncall_cnt
                cnt_for_tbl.ENGEL_COUNT = ln_engel_cnt
                cnt_for_tbl.NENKYU = ln_nenkyu
                cnt_for_tbl.NENKYU_HALF = ln_nenkyu_half
                cnt_for_tbl.TIKOKU = ln_tikoku
                cnt_for_tbl.SOUTAI = ln_soutai
                cnt_for_tbl.KEKKIN = ln_kekkin
                cnt_for_tbl.SYUTTYOU = ln_syuttyou
                cnt_for_tbl.SYUTTYOU_HALF = ln_syuttyou_half
                cnt_for_tbl.REFLESH = ln_reflesh
                cnt_for_tbl.MILEAGE = ln_s_kyori
                cnt_for_tbl.SUM_WORKTIME = working_time
                cnt_for_tbl.OVERTIME = over
                cnt_for_tbl.HOLIDAY_WORK = holiday_work
                cnt_for_tbl.WORKDAY_COUNT = workday_count
                cnt_for_tbl.SUM_WORKTIME_10 = working_time_10
                cnt_for_tbl.OVERTIME_10= over_10
                cnt_for_tbl.HOLIDAY_WORK_10 = holiday_work_10
                cnt_for_tbl.TIMEOFF = timeoff
                cnt_for_tbl.HALFWAY_THROUGH = halfway_through
                
                db.session.commit()



    else:
        y = datetime.today().year
        m = datetime.today().month

        for user in users:
            staffid = user.STAFFID
            shinseis = Shinsei.query.filter_by(STAFFID=staffid).all()
            u = User.query.get(staffid)
            rp_holiday = RecordPaidHoliday.query.get(staffid)
            tm_attendance = TimeAttendance.query.get(staffid)
            cnt_for_tbl = CounterForTable.query.get(staffid)
            
            

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
            
            timeoff1 = []
            timeoff2 = []
            timeoff3 = []
            halfway_through1 = []
            halfway_through2 = []
            halfway_through3 = []   

            for sh in shinseis:

                # パートの場合
                if u.CONTRACT_CODE == 2:

                    ##### 月間実働時間（２６日基準） #####
                    if m == 1:  # 1月
                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if (datetime(y, m, 1) >= base_day) and (datetime(y - 1, m + 11, 25) < base_day):
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
                        if (datetime(y, m, 25) >= base_day) and (datetime(y, m - 1, 25) < base_day):
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
                        if (datetime(y, m, 25) >= base_day) and (datetime(y, m - 1, 25) < base_day):                        
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
                        if (datetime(y, m, 25) >= base_day) and (datetime(y, m - 1, 25) < base_day):                        
                        
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
                        if (datetime(y, m, 25) >= base_day) and (datetime(y, m - 1, 25) < base_day):                        
                        
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
                        if (datetime(y, m, 25) >= base_day) and (datetime(y, m - 1, 25) < base_day):                        
                        
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
                        if (datetime(y, m, 25) >= base_day) and (datetime(y, m - 1, 25) < base_day):                        
                        
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
                        if (datetime(y, m, 25) >= base_day) and (datetime(y, m - 1, 25) < base_day):                        
                        
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
                        if (datetime(y, m, 25) >= base_day) and (datetime(y, m - 1, 25) < base_day):                        
                        
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
                        if (datetime(y, m, 25) >= base_day) and (datetime(y, m - 1, 25) < base_day):                        
                        
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
                        if (datetime(y, m, 25) >= base_day) and (datetime(y, m - 1, 25) < base_day):                        
                        
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
                        if (datetime(y, m, 25) >= base_day) and (datetime(y, m - 1, 25) < base_day):                        
                        
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
                        if (datetime(y, m, 1) >= base_day) and (datetime(y - 1, m + 11, 25) < base_day):
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
                                
                            if sh.NOTIFICATION == "10" or sh.NOTIFICATION2 == "10":
                                timeoff1.append(cnt1)
                            if sh.NOTIFICATION == "11" or sh.NOTIFICATION2 == "11":
                                timeoff2.append(cnt2)
                            if sh.NOTIFICATION == "12" or sh.NOTIFICATION2 == "12":
                                timeoff3.append(cnt3)
                            if sh.NOTIFICATION == "13" or sh.NOTIFICATION2 == "13":
                                halfway_through1.append(cnt01)
                            if sh.NOTIFICATION == "14" or sh.NOTIFICATION2 == "14":
                                halfway_through2.append(cnt02)
                            if sh.NOTIFICATION == "15" or sh.NOTIFICATION2 == "15":
                                halfway_through3.append(cnt03)

                    if m == 2:  # ２月
                        if y % 4 == 0:
                            d = 29
                        elif y % 4 != 0:
                            d = 28

                        base_day = datetime.strptime(sh.WORKDAY, '%Y-%m-%d')
                        if (datetime(y, m, 25) >= base_day) and (datetime(y, m - 1, 25) < base_day):
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
                                
                            if sh.NOTIFICATION == "10" or sh.NOTIFICATION2 == "10":
                                timeoff1.append(cnt1)
                            if sh.NOTIFICATION == "11" or sh.NOTIFICATION2 == "11":
                                timeoff2.append(cnt2)
                            if sh.NOTIFICATION == "12" or sh.NOTIFICATION2 == "12":
                                timeoff3.append(cnt3)
                            if sh.NOTIFICATION == "13" or sh.NOTIFICATION2 == "13":
                                halfway_through1.append(cnt01)
                            if sh.NOTIFICATION == "14" or sh.NOTIFICATION2 == "14":
                                halfway_through2.append(cnt02)
                            if sh.NOTIFICATION == "15" or sh.NOTIFICATION2 == "15":
                                halfway_through3.append(cnt03)

                    if m == 3:  # ３月
                        d = 31
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                               sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                               oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                               tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)
                        dft26.other_data26()

                        tm_off = TimeOffClass(y, m, d, sh.WORKDAY, sh.NOTIFICATION, sh.NOTIFICATION2, timeoff1, timeoff2, timeoff3,
                                            halfway_through1, halfway_through2, halfway_through3)
                        tm_off.cnt_time_off()

                    if m == 4:  # ４月
                        d = 30
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                               sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                               oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                               tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                        tm_off = TimeOffClass(y, m, d, sh.WORKDAY, sh.NOTIFICATION, sh.NOTIFICATION2, timeoff1, timeoff2, timeoff3,
                                            halfway_through1, halfway_through2, halfway_through3)
                        tm_off.cnt_time_off()

                    if m == 5:  # ５月
                        d = 31
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                               sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                               oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                               tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                        tm_off = TimeOffClass(y, m, d, sh.WORKDAY, sh.NOTIFICATION, sh.NOTIFICATION2, timeoff1, timeoff2, timeoff3,
                                            halfway_through1, halfway_through2, halfway_through3)
                        tm_off.cnt_time_off()

                    if m == 6:  # ６月
                        d = 30
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                               sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                               oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                               tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                        tm_off = TimeOffClass(y, m, d, sh.WORKDAY, sh.NOTIFICATION, sh.NOTIFICATION2, timeoff1, timeoff2, timeoff3,
                                            halfway_through1, halfway_through2, halfway_through3)
                        tm_off.cnt_time_off()

                    if m == 7:  # ７月
                        d = 31
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                               sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                               oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                               tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                        tm_off = TimeOffClass(y, m, d, sh.WORKDAY, sh.NOTIFICATION, sh.NOTIFICATION2, timeoff1, timeoff2, timeoff3,
                                            halfway_through1, halfway_through2, halfway_through3)
                        tm_off.cnt_time_off()

                    if m == 8:  # ８月
                        d = 31
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                               sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                               oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                               tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                        tm_off = TimeOffClass(y, m, d, sh.WORKDAY, sh.NOTIFICATION, sh.NOTIFICATION2, timeoff1, timeoff2, timeoff3,
                                            halfway_through1, halfway_through2, halfway_through3)
                        tm_off.cnt_time_off()

                    if m == 9:  # ９月
                        d = 30
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                               sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                               oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                               tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                        tm_off = TimeOffClass(y, m, d, sh.WORKDAY, sh.NOTIFICATION, sh.NOTIFICATION2, timeoff1, timeoff2, timeoff3,
                                            halfway_through1, halfway_through2, halfway_through3)
                        tm_off.cnt_time_off()

                    if m == 10:  # １０月
                        d = 31
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                               sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                               oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                               tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                        tm_off = TimeOffClass(y, m, d, sh.WORKDAY, sh.NOTIFICATION, sh.NOTIFICATION2, timeoff1, timeoff2, timeoff3,
                                            halfway_through1, halfway_through2, halfway_through3)
                        tm_off.cnt_time_off()

                    if m == 11:  # １１月
                        d = 30
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                               sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                               oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                               tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                        tm_off = TimeOffClass(y, m, d, sh.WORKDAY, sh.NOTIFICATION, sh.NOTIFICATION2, timeoff1, timeoff2, timeoff3,
                                            halfway_through1, halfway_through2, halfway_through3)
                        tm_off.cnt_time_off()

                    if m == 12:  # １２月
                        d = 31
                        dft26 = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                               sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                               oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half,
                                               tikoku, soutai, kekkin, syuttyou, syuttyou_half, reflesh, s_kyori)

                        dft26.other_data26()

                        tm_off = TimeOffClass(y, m, d, sh.WORKDAY, sh.NOTIFICATION, sh.NOTIFICATION2, timeoff1, timeoff2, timeoff3,
                                            halfway_through1, halfway_through2, halfway_through3)
                        tm_off.cnt_time_off()


            ##### データベース貯蔵 #####
            ln_oncall = len(oncall)
            ln_oncall_holiday = len(oncall_holiday)

            ln_oncall_cnt = 0
            for oc in oncall_cnt:
                ln_oncall_cnt += int(oc)
                
            ln_engel_cnt= 0
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
            
            sum_timeoff1 = len(timeoff1)
            sum_timeoff2 = len(timeoff2)
            sum_timeoff3 = len(timeoff3)
            timeoff = sum_timeoff1 + sum_timeoff2 * 2 + sum_timeoff3 * 3
            
            sum_halfway_through1 = len(halfway_through1)
            sum_halfway_through2 = len(halfway_through2)
            sum_halfway_through3 = len(halfway_through3)
            halfway_through = sum_halfway_through1 + sum_halfway_through2 * 2 + sum_halfway_through3 * 3


            if cnt_for_tbl:
                cnt_for_tbl.ONCALL = ln_oncall
                cnt_for_tbl.ONCALL_HOLIDAY = ln_oncall_holiday
                cnt_for_tbl.ONCALL_COUNT = ln_oncall_cnt
                cnt_for_tbl.ENGEL_COUNT = ln_engel_cnt
                cnt_for_tbl.NENKYU = ln_nenkyu
                cnt_for_tbl.NENKYU_HALF = ln_nenkyu_half
                cnt_for_tbl.TIKOKU = ln_tikoku
                cnt_for_tbl.SOUTAI = ln_soutai
                cnt_for_tbl.KEKKIN = ln_kekkin
                cnt_for_tbl.SYUTTYOU = ln_syuttyou
                cnt_for_tbl.SYUTTYOU_HALF = ln_syuttyou_half
                cnt_for_tbl.REFLESH = ln_reflesh
                cnt_for_tbl.MILEAGE = ln_s_kyori
                cnt_for_tbl.SUM_WORKTIME = working_time
                cnt_for_tbl.OVERTIME = over
                cnt_for_tbl.HOLIDAY_WORK = holiday_work
                cnt_for_tbl.WORKDAY_COUNT = workday_count
                cnt_for_tbl.SUM_WORKTIME_10 = working_time_10
                cnt_for_tbl.OVERTIME_10= over_10
                cnt_for_tbl.HOLIDAY_WORK_10 = holiday_work_10
                cnt_for_tbl.TIMEOFF = timeoff
                cnt_for_tbl.HALFWAY_THROUGH = halfway_through
                
                db.session.commit()



        return render_template('attendance/jimu_summary_parttime26.html', typ=typ, form_month=form_month, workday_data=workday_data, y=y, m=m, dwl_today=dwl_today,
                               users=users, cfts=cfts, str_workday=str_workday, bumon=bumon, syozoku=syozoku, syokusyu=syokusyu, keitai=keitai,
                               jimu_usr=jimu_usr, stf_login=stf_login, workday_count=workday_count,
                               timeoff=timeoff, halfway_rough=halfway_through)

    return render_template('attendance/jimu_summary_parttime26.html', typ=typ, form_month=form_month, workday_data=workday_data, y=y, m=m, dwl_today=dwl_today,
                           users=users, cfts=cfts, str_workday=str_workday, bumon=bumon, syozoku=syozoku, syokusyu=syokusyu, keitai=keitai,
                           jimu_usr=jimu_usr, stf_login=stf_login, workday_count=workday_count,
                           timeoff=timeoff, halfway_rough=halfway_through)


##### パート１日基準 #####
@app.route('/jimu_summary_parttime', methods=['GET', 'POST'])
@login_required
def jimu_summary_parttime():
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    typ = ["submit", "text", "time", "checkbox", "number", "date"]
    form_month = SelectMonthForm()

    workday_data = ""
    str_workday = "月選択をしてください。"
    str_workday = "月選択をしてください"
    bumon = ["本社", "宇介", "下介", "鹿介", "KO介", "宇福", "KO福", "鹿福", "筑波介"]
    syozoku = ["本社", "宇都宮", "下野", "鹿沼", "KODOMOTO", "在宅支援", "KOそうだん", "つくば"]
    syokusyu = ["NS", "事務", "OT", "ST", "PT",
                "相談専門", "相談補助", "保育支援", "准NS", "開発", "広報"]
    keitai = ["8H", "パート", "6H", "7H", "32H"]
    y = ""
    m = ""
    outer_display = 0
    
    dwl_today = datetime.today()    

    users = User.query.all()
    cfts = CounterForTable.query.all()
    
    jimu_usr = User.query.get(current_user.STAFFID)

    if form_month.validate_on_submit():
        selected_workday = request.form.get('workday_name')

        if selected_workday:
            y = datetime.strptime(selected_workday, '%Y-%m').year
            m = datetime.strptime(selected_workday, '%Y-%m').month
        else:
            y = datetime.today().year
            m = datetime.today().month

        session['workday_data'] = selected_workday
        workday_data = session['workday_data']

        for user in users:
            staffid = user.STAFFID
            shinseis = Shinsei.query.filter_by(STAFFID=staffid).all()
            u = User.query.get(staffid)
            cnt_for_tbl = CounterForTable.query.get(staffid)
            rp_holiday = RecordPaidHoliday.query.get(staffid)
            tm_attendance = TimeAttendance.query.get(staffid)
            
            

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
            
            timeoff1 = []
            timeoff2 = []
            timeoff3 = []
            halfway_through1 = []
            halfway_through2 = []
            halfway_through3 = []   
 

            for sh in shinseis:

                # パートタイマーの場合
                if u.CONTRACT_CODE == 2:
                    ##### １日基準 #####
                    d = get_last_date(y, m)

                    dft = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                        sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                        oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half, tikoku, soutai, kekkin,
                                        syuttyou, syuttyou_half, reflesh, s_kyori)
                    dft.other_data()

                    tm_off = TimeOffClass(y, m, d, sh.WORKDAY, sh.NOTIFICATION, sh.NOTIFICATION2, timeoff1, timeoff2, timeoff3,
                                        halfway_through1, halfway_through2, halfway_through3)
                    tm_off.cnt_time_off()

                

                    # 労働時間系統
                    d = get_last_date(y, m)

                    if datetime(y, m, 1) <= datetime.strptime(sh.WORKDAY, '%Y-%m-%d') and datetime(y, m, d) >= datetime.strptime(sh.WORKDAY, '%Y-%m-%d'):
                        dtm = datetime.strptime(sh.ENDTIME, '%H:%M') - datetime.strptime(sh.STARTTIME, '%H:%M')

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

               
            ##### データベース貯蔵 #####
            ln_oncall = len(oncall)
            ln_oncall_holiday = len(oncall_holiday)

            ln_oncall_cnt = 0
            for oc in oncall_cnt:
                ln_oncall_cnt += int(oc)
                
            ln_engel_cnt= 0
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
            
            sum_timeoff1 = len(timeoff1)
            sum_timeoff2 = len(timeoff2)
            sum_timeoff3 = len(timeoff3)
            timeoff = sum_timeoff1 + sum_timeoff2 * 2 + sum_timeoff3 * 3
            
            sum_halfway_through1 = len(halfway_through1)
            sum_halfway_through2 = len(halfway_through2)
            sum_halfway_through3 = len(halfway_through3)
            halfway_through = sum_halfway_through1 + sum_halfway_through2 * 2 + sum_halfway_through3 * 3


            if cnt_for_tbl:
                cnt_for_tbl.ONCALL = ln_oncall
                cnt_for_tbl.ONCALL_HOLIDAY = ln_oncall_holiday
                cnt_for_tbl.ONCALL_COUNT = ln_oncall_cnt
                cnt_for_tbl.ENGEL_COUNT = ln_engel_cnt
                cnt_for_tbl.NENKYU = ln_nenkyu
                cnt_for_tbl.NENKYU_HALF = ln_nenkyu_half
                cnt_for_tbl.TIKOKU = ln_tikoku
                cnt_for_tbl.SOUTAI = ln_soutai
                cnt_for_tbl.KEKKIN = ln_kekkin
                cnt_for_tbl.SYUTTYOU = ln_syuttyou
                cnt_for_tbl.SYUTTYOU_HALF = ln_syuttyou_half
                cnt_for_tbl.REFLESH = ln_reflesh
                cnt_for_tbl.MILEAGE = ln_s_kyori
                cnt_for_tbl.SUM_WORKTIME = working_time
                cnt_for_tbl.OVERTIME = over
                cnt_for_tbl.HOLIDAY_WORK = holiday_work
                cnt_for_tbl.WORKDAY_COUNT = workday_count
                cnt_for_tbl.SUM_WORKTIME_10 = working_time_10
                cnt_for_tbl.OVERTIME_10= over_10
                cnt_for_tbl.HOLIDAY_WORK_10 = holiday_work_10
                cnt_for_tbl.TIMEOFF = timeoff
                cnt_for_tbl.HALFWAY_THROUGH = halfway_through
                
                db.session.commit()
                
            ##### 退職者表示設定
             
                

    else:
        y = datetime.today().year
        m = datetime.today().month

        for user in users:
            staffid = user.STAFFID
            shinseis = Shinsei.query.filter_by(STAFFID=staffid).all()
            u = User.query.get(staffid)
            cnt_for_tbl = CounterForTable.query.get(staffid)
            rp_holiday = RecordPaidHoliday.query.get(staffid)
            tm_attendance = TimeAttendance.query.get(staffid)
            
            

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
            
            timeoff1 = []
            timeoff2 = []
            timeoff3 = []
            halfway_through1 = []
            halfway_through2 = []
            halfway_through3 = []   


            for sh in shinseis:

                # パートの場合
                if u.CONTRACT_CODE == 2:
                    ##### １日基準 #####
                    d = get_last_date(y, m)


                    dft = DataForTable(y, m, d, sh.WORKDAY, sh.ONCALL, sh.HOLIDAY, sh.ONCALL_COUNT, sh.ENGEL_COUNT,
                                        sh.NOTIFICATION, sh.NOTIFICATION2, sh.MILEAGE,
                                        oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half, tikoku, soutai, kekkin,
                                        syuttyou, syuttyou_half, reflesh, s_kyori)
                    dft.other_data()

                    tm_off = TimeOffClass(y, m, d, sh.WORKDAY, sh.NOTIFICATION, sh.NOTIFICATION2, timeoff1, timeoff2, timeoff3,
                                        halfway_through1, halfway_through2, halfway_through3)
                    tm_off.cnt_time_off()


                    # 労働時間系統

                    d = get_last_date(y, m)

                    if datetime(y, m, 1) <= datetime.strptime(sh.WORKDAY, '%Y-%m-%d') and datetime(y, m, d) >= datetime.strptime(sh.WORKDAY, '%Y-%m-%d'):
                        dtm = datetime.strptime(sh.ENDTIME, '%H:%M') - datetime.strptime(sh.STARTTIME, '%H:%M')

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


            ##### データベース貯蔵 #####
            ln_oncall = len(oncall)
            ln_oncall_holiday = len(oncall_holiday)

            ln_oncall_cnt = 0
            for oc in oncall_cnt:
                ln_oncall_cnt += int(oc)
                
            ln_engel_cnt= 0
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
            
            sum_timeoff1 = len(timeoff1)
            sum_timeoff2 = len(timeoff2)
            sum_timeoff3 = len(timeoff3)
            timeoff = sum_timeoff1 + sum_timeoff2 * 2 + sum_timeoff3 * 3
            
            sum_halfway_through1 = len(halfway_through1)
            sum_halfway_through2 = len(halfway_through2)
            sum_halfway_through3 = len(halfway_through3)
            halfway_through = sum_halfway_through1 + sum_halfway_through2 * 2 + sum_halfway_through3 * 3


            if cnt_for_tbl:
                cnt_for_tbl.ONCALL = ln_oncall
                cnt_for_tbl.ONCALL_HOLIDAY = ln_oncall_holiday
                cnt_for_tbl.ONCALL_COUNT = ln_oncall_cnt
                cnt_for_tbl.ENGEL_COUNT = ln_engel_cnt
                cnt_for_tbl.NENKYU = ln_nenkyu
                cnt_for_tbl.NENKYU_HALF = ln_nenkyu_half
                cnt_for_tbl.TIKOKU = ln_tikoku
                cnt_for_tbl.SOUTAI = ln_soutai
                cnt_for_tbl.KEKKIN = ln_kekkin
                cnt_for_tbl.SYUTTYOU = ln_syuttyou
                cnt_for_tbl.SYUTTYOU_HALF = ln_syuttyou_half
                cnt_for_tbl.REFLESH = ln_reflesh
                cnt_for_tbl.MILEAGE = ln_s_kyori
                cnt_for_tbl.SUM_WORKTIME = working_time
                cnt_for_tbl.OVERTIME = over
                cnt_for_tbl.HOLIDAY_WORK = holiday_work
                cnt_for_tbl.WORKDAY_COUNT = workday_count
                cnt_for_tbl.SUM_WORKTIME_10 = working_time_10
                cnt_for_tbl.OVERTIME_10= over_10
                cnt_for_tbl.HOLIDAY_WORK_10 = holiday_work_10
                cnt_for_tbl.TIMEOFF = timeoff
                cnt_for_tbl.HALFWAY_THROUGH = halfway_through
                
                db.session.commit()
                
            ##### 退職者表示設定
              


        return render_template('attendance/jimu_summary_parttime.html', typ=typ, form_month=form_month, workday_data=workday_data, y=y, m=m, dwl_today=dwl_today,
                               users=users, cfts=cfts, str_workday=str_workday, bumon=bumon, syozoku=syozoku, syokusyu=syokusyu,
                               keitai=keitai, jimu_usr=jimu_usr, stf_login=stf_login, workday_count=workday_count,
                               timeoff=timeoff, halfway_rough=halfway_through)

    return render_template('attendance/jimu_summary_parttime.html', typ=typ, form_month=form_month, workday_data=workday_data, y=y, m=m, dwl_today=dwl_today,
                           users=users, cfts=cfts, str_workday=str_workday, bumon=bumon, syozoku=syozoku, syokusyu=syokusyu,
                           keitai=keitai, jimu_usr=jimu_usr, stf_login=stf_login, workday_count=workday_count,
                           timeoff=timeoff, halfway_rough=halfway_through)


@app.route('/jimu_nenkyu_detail/<STAFFID>', methods=['GET', 'POST'])
@login_required
def jimu_nenkyu_detail(STAFFID):
    stf_login = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    STAFFID = STAFFID
    user = User.query.get(STAFFID)
    rp_holiday = RecordPaidHoliday.query.get(STAFFID)
    shinseis = Shinsei.query.filter(Shinsei.STAFFID==STAFFID).all()
    cnt_attendance = CountAttendance.query.get(STAFFID)
    tm_attendance = TimeAttendance.query.get(STAFFID)

    next_datagrant = rp_holiday.NEXT_DATEGRANT - timedelta(days=1)

                
    ##### 今回付与日数 #####
    inday = rp_holiday.INDAY
    
    def nenkyu_days(a, h, s):                                  
        
        if rp_holiday.LAST_DATEGRANT is None:
            shinseis = Shinsei.query.filter(Shinsei.STAFFID==STAFFID).filter(Shinsei.NOTIFICATION=="3").all()
            for shs in shinseis:
                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= inday and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                    nenkyu_all_days.add(shs.WORKDAY)
                    
            shinseis = Shinsei.query.filter(Shinsei.STAFFID==STAFFID).filter(Shinsei.NOTIFICATION=="4").all()
            for shs in shinseis:
                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= inday and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                    nenkyu_half_days.add(shs.WORKDAY)
            
            shinseis = Shinsei.query.filter(Shinsei.STAFFID==STAFFID).filter(Shinsei.NOTIFICATION=="16").all()
            for shs in shinseis:
                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= inday and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                    seiri_days.append(shs.WORKDAY)
                
            shinseis = Shinsei.query.filter(Shinsei.STAFFID==STAFFID).filter(Shinsei.NOTIFICATION2=="4").all()
            for shs in shinseis:
                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= inday and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                    nenkyu_half_days.add(shs.WORKDAY)
            
            shinseis = Shinsei.query.filter(Shinsei.STAFFID==STAFFID).filter(Shinsei.NOTIFICATION2=="16").all()
            for shs in shinseis:
                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= inday and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                    seiri_days.append(shs.WORKDAY)
        
        else:
            shinseis = Shinsei.query.filter(Shinsei.STAFFID==STAFFID).filter(Shinsei.NOTIFICATION=="3").all()
            for shs in shinseis:
                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                    nenkyu_all_days.add(shs.WORKDAY)
                    
            shinseis = Shinsei.query.filter(Shinsei.STAFFID==STAFFID).filter(Shinsei.NOTIFICATION=="4").all()
            for shs in shinseis:
                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                    nenkyu_half_days.add(shs.WORKDAY)
            
            shinseis = Shinsei.query.filter(Shinsei.STAFFID==STAFFID).filter(Shinsei.NOTIFICATION=="16").all()
            for shs in shinseis:
                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                    seiri_days.append(shs.WORKDAY)
                
            shinseis = Shinsei.query.filter(Shinsei.STAFFID==STAFFID).filter(Shinsei.NOTIFICATION2=="4").all()
            for shs in shinseis:
                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                    nenkyu_half_days.add(shs.WORKDAY)
            
            shinseis = Shinsei.query.filter(Shinsei.STAFFID==STAFFID).filter(Shinsei.NOTIFICATION2=="16").all()
            for shs in shinseis:
                if datetime.strptime(shs.WORKDAY, '%Y-%m-%d') >= rp_holiday.LAST_DATEGRANT and datetime.strptime(shs.WORKDAY, '%Y-%m-%d') < rp_holiday.NEXT_DATEGRANT:
                    seiri_days.append(shs.WORKDAY)
                                       
                    
        return nenkyu_all_days, nenkyu_half_days, seiri_days
    
    
    if inday.month == 4 and inday.month == 5:
        first_day = inday.replacereplace(month=4, day=1)
    elif inday.month == 6 and inday.month == 7:
        first_day = inday.replacereplace(month=4, day=1)
    elif inday.month == 8 and inday.month == 9:
        first_day = inday.replacereplace(month=4, day=1)
    elif inday.month == 10 and inday.month == 11:
        first_day = inday.replace(month=4, day=1)
    elif inday.month == 12 and inday.month == 1:
        first_day = inday.replace(month=4, day=1)
    elif inday.month == 2 and inday.month == 3:
        first_day = inday.replace(month=4, day=1)
        
    ddm = monthmod(inday, datetime.today())[0].months    
    dm = monthmod(inday, rp_holiday.LAST_DATEGRANT)[0].months
    
    """ 常勤 """
    if rp_holiday.CONTRACT_CODE != 2:

        ##### 年休付与日数設定 #####
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
            elif dm < 76:
                aquisition_days = 18
            elif dm >= 76:
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
        enable_days = aquisition_days + rp_holiday.LAST_CARRIEDOVER # 使用可能日数
        
        ##### 取得日　取得日数　年休種類 #####
        nenkyu_all_days = set()
        nenkyu_half_days = set()
        seiri_days = set()

        nenkyu_days(nenkyu_all_days, nenkyu_half_days, seiri_days)
                        
        x = len(nenkyu_all_days) + len(nenkyu_half_days) * 0.5 + len(seiri_days) * 0.5 # 年休使用日数 

        if rp_holiday.USED_PAIDHOLIDAY is None:
            rp_holiday(USED_PAIDHOLIDAY=x)
            db.session.add(rp_holiday)
            db.session.commit()
        else:
            rp_holiday.USED_PAIDHOLIDAY = x
            db.session.commit()

        y = rp_holiday.LAST_CARRIEDOVER + aquisition_days - x # 年休残日数
        if y < 0:
            y = 0                                                 
      

        """ パート """                            
    elif rp_holiday.CONTRACT_CODE == 2:

        aquisition_days = 0 # 簡易的に記載
        enable_days = 0 # 簡易的に記載
        
        ##### 取得日　取得日数　年休種類 #####
        nenkyu_all_days = set()
        nenkyu_half_days = set()
        seiri_days = set()

        nenkyu_days(nenkyu_all_days, nenkyu_half_days, seiri_days)
                        
        x = len(nenkyu_all_days) + len(nenkyu_half_days) * 0.5 + len(seiri_days) * 0.5 # 年休使用日数 

        if rp_holiday.USED_PAIDHOLIDAY is None:
            rp_holiday(USED_PAIDHOLIDAY=x)
            db.session.add(rp_holiday)
            db.session.commit()
        else:
            rp_holiday.USED_PAIDHOLIDAY = x
            db.session.commit()
            
        y = rp_holiday.LAST_CARRIEDOVER + aquisition_days - x # 年休残日数
        if y < 0:
            y = 0        
            
    return render_template('attendance/jimu_nenkyu_detail.html', user=user, rp_holiday=rp_holiday, aquisition_days=aquisition_days,
                           next_datagrant=next_datagrant, nenkyu_all_days=nenkyu_all_days, nenkyu_half_days=nenkyu_half_days,
                           enable_days=enable_days, cnt_attendance=cnt_attendance, tm_attendance=tm_attendance,
                           seiri_days=seiri_days, stf_login=stf_login)

