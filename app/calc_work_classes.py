"""
**********
勤怠システム
2022/04版
**********
"""

from flask import render_template, flash, redirect, request, session
from werkzeug.urls import url_parse
from flask.helpers import url_for
from flask_login.utils import login_required
from app import app, db
from app.forms import LoginForm, AdminUserCreateForm, ResetPasswordForm, DelForm, UpdateForm, SaveForm, AddDataUserForm, SelectMonthForm
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
import calendar
from dateutil.relativedelta import relativedelta
from monthdelta import monthmod
from app.models import D_JOB_HISTORY, D_HOLIDAY_HISTORY, KinmuTaisei


os.environ.get('SECRET_KEY') or 'you-will-never-guess'
app.permanent_session_lifetime = timedelta(minutes=360)


#***** 管理者か判断 *****#

def admin_login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_admin():
            return abort(403)
        return func(*args, **kwargs)
    return decorated_view

#***** 年月から最終日を返す*****#
def get_last_date(year, month):
    return calendar.monthrange(year, month)[1]



#***** 各勤怠カウント計算ひな形（１日基準） *****#
class DataForTable:
    def __init__(self, y, m, d, sh_workday, sh_oncall, sh_holiday, sh_oncall_count, sh_engel_count, sh_notification, sh_notification_pm,
                 sh_mileage, oncall, oncall_holiday, oncall_cnt, engel_cnt, nenkyu, nenkyu_half, tikoku, soutai, kekkin,
                 syuttyou, syuttyou_half, reflesh, s_kyori, startday, today):
        self.y = y
        self.m = m
        self.d = d
        self.sh_workday = sh_workday
        self.sh_oncall = sh_oncall
        self.sh_holiday = sh_holiday
        self.sh_oncall_count = sh_oncall_count
        self.sh_engel_count = sh_engel_count
        self.sh_notification = sh_notification
        self.sh_notification_pm = sh_notification_pm
        self.sh_mileage = sh_mileage
        self.oncall = oncall
        self.oncall_holiday = oncall_holiday
        self.oncall_cnt = oncall_cnt
        self.engel_cnt = engel_cnt
        self.nenkyu = nenkyu
        self.nenkyu_half = nenkyu_half
        self.tikoku = tikoku
        self.soutai = soutai
        self.kekkin = kekkin
        self.syuttyou = syuttyou
        self.syuttyou_half = syuttyou_half
        self.reflesh = reflesh
        self.s_kyori = s_kyori
        self.startday = startday
        self.today = today

    def other_data(self):
        if self.startday <= datetime.strptime(self.sh_workday, '%Y-%m-%d') and \
            self.today >= datetime.strptime(self.sh_workday, '%Y-%m-%d'):
                # オンコール当番
                if self.sh_oncall == '1' and self.sh_holiday == "1":
                    # 土日オンコール当番
                    self.oncall_holiday.append("cnt")
                elif self.sh_oncall == "1":
                    self.oncall.append("cnt")
                    
                # オンコール対応件数
                if self.sh_oncall_count:
                    self.oncall_cnt.append(str(self.sh_oncall_count))
                # エンゼルケア対応件数
                if self.sh_engel_count:
                    self.engel_cnt.append(str(self.sh_engel_count))
                # 年休日数（全日）
                if self.sh_notification == "3":
                    self.nenkyu.append("cnt")
                # 年休日数（半日）
                if self.sh_notification == "4" or self.sh_notification == "16":
                    self.nenkyu_half.append("cnt")
                # 年休日数（半日）
                if self.sh_notification_pm == "4" or self.sh_notification_pm == "16":
                    self.nenkyu_half.append("cnt")                   
                # 遅刻回数
                if self.sh_notification == "1":
                    self.tikoku.append("cnt")
                # 遅刻回数
                if self.sh_notification_pm == "1":
                    self.tikoku.append("cnt")
                # 早退回数
                if self.sh_notification == "2":
                    self.soutai.append("cnt")
                # 早退回数
                if self.sh_notification_pm == "2":
                    self.soutai.append("cnt")
                # 欠勤日数
                if self.sh_notification == "8" or self.sh_notification == "17" or self.sh_notification == "18" or self.sh_notification == "19" or self.sh_notification == "20":
                    self.kekkin.append("cnt")
                # 出張（全日）回数
                if self.sh_notification == "5":
                    self.syuttyou.append("cnt")
                # 出張（半日）回数
                if self.sh_notification == "6":
                    self.syuttyou_half.append("cnt")
                # 出張（半日）回数
                if self.sh_notification_pm == "6":
                    self.syuttyou_half.append("cnt")
                # リフレッシュ休暇日数
                if self.sh_notification == "7":
                    self.reflesh.append("cnt")
                # 走行距離
                if self.sh_mileage:
                    self.s_kyori.append(str(self.sh_mileage))




#***** 常勤用各勤怠時間計算ひな形 *****#
class CalcTimeClass:
    def __init__(self, t, sh_notification, sh_notification_pm, sh_starttime, sh_endtime, sh_overtime, u_contract_code,
                 syukkin_times_0, over_time_0, rp_holiday_basetime_paidholiday, real_time, real_time_sum,
                 syukkin_holiday_times_0, sh_holiday, sh_jobtype, staffid, workday):
        self.t = t
        self.sh_notification = sh_notification
        self.sh_notification_pm = sh_notification_pm
        self.sh_starttime = sh_starttime
        self.sh_endtime = sh_endtime
        self.sh_overtime = sh_overtime
        self.u_contract_code = u_contract_code
        self.syukkin_times_0 = syukkin_times_0
        self.over_time_0 = over_time_0
        self.rp_holiday_basetime_paidholiday = rp_holiday_basetime_paidholiday
        self.real_time = real_time
        self.real_time_sum = real_time_sum
        self.syukkin_holiday_times_0 = syukkin_holiday_times_0
        self.holiday = sh_holiday
        self.jobtype = sh_jobtype
        self.staffid = staffid
        self.workday = workday
        rest = 0
        worktime = 0
        

    def calc_time(self):

        #実働時間の算出
        if  self.jobtype != 12 and self.sh_starttime != "00:00" and datetime.strptime(self.sh_starttime, '%H:%M') < datetime.strptime("08:00", '%H:%M'):
            self.sh_starttime = "08:00"
        self.t  = datetime.strptime(self.sh_endtime, '%H:%M') - datetime.strptime(self.sh_starttime, '%H:%M')
        self.real_time = self.t
        # 残業判断の基準となる時間

        Contracts = D_JOB_HISTORY.query.filter_by(STAFFID=self.staffid).order_by(D_JOB_HISTORY.START_DAY).all()
     #   fruits = (
     #       db.session.query(D_CONTRACT_HISTORY, KinmuTaisei.TEMPLATE_NO)
     #       .filter(D_CONTRACT_HISTORY.STAFFID == self.staffid, 
     #               D_CONTRACT_HISTORY.CONTACT_CODE == KinmuTaisei.CODE)
     #       .order_by(D_CONTRACT_HISTORY.START_DAY)
     #       .all()
     #   )
        # 表示期間の契約状況
        for row in Contracts:
            # 契約の適用終了が日付型じゃない(Null)。終わりがなく現在適用中
            if datetime.strptime(self.workday, '%Y-%m-%d') >= datetime.strptime(str(row.START_DAY), '%Y-%m-%d') and \
                not isinstance(row.END_DAY, date):
                intContract = row.CONTACT_CODE
                parttime = row.PART_WORKTIME
                
                break
            elif datetime.strptime(self.workday, '%Y-%m-%d') >= datetime.strptime(str(row.START_DAY), '%Y-%m-%d') and \
                datetime.strptime(self.workday, '%Y-%m-%d') <= datetime.strptime(str(row.END_DAY), '%Y-%m-%d'):
                intContract = row.CONTACT_CODE
                parttime = row.PART_WORKTIME
               
                break
       
        # 今だけ暫定
        intContract = self.u_contract_code

        # 表示期間の年休単位
        Holidaytime = D_HOLIDAY_HISTORY.query.filter_by(STAFFID=self.staffid).order_by(D_HOLIDAY_HISTORY.START_DAY).all()

        for row in Holidaytime:
            # 契約の適用終了が日付型じゃない(Null)。終わりがなく現在適用中
            if not isinstance(row.END_DAY, date):
                intHolidaytime = row.HOLIDAY_TIME
                
                break
            elif datetime.strptime(self.workday, '%Y-%m-%d') >= datetime.strptime(str(row.START_DAY), '%Y-%m-%d') and \
                datetime.strptime(self.workday, '%Y-%m-%d') <= datetime.strptime(str(row.END_DAY), '%Y-%m-%d'):
                intHolidaytime = row.HOLIDAY_TIME
                
                break        
        # 今だけ暫定
        intHolidaytime = self.rp_holiday_basetime_paidholiday

        # 8時間常勤、32H常勤
        if intContract == 1 or intContract == 5:
            worktime = 8
        # 7時間常勤
        elif intContract == 4:
            worktime = 7
        # 6時間常勤
        elif intContract == 3:
            worktime = 6
        # パート
        elif intContract == 2:
            #今だけ worktime =  parttime
            worktime = 8
        
        # AM時間休
        if self.sh_notification == "10":
            self.t = self.t + timedelta(hours=1)
        elif self.sh_notification == "11":
            self.t = self.t + timedelta(hours=2)
        elif self.sh_notification == "12":
            self.t = self.t + timedelta(hours=3)

        # PM時間休
        if self.sh_notification_pm == "10":
            self.t = self.t + timedelta(hours=1)
        elif self.sh_notification_pm == "11":
            self.t = self.t + timedelta(hours=2)
        elif self.sh_notification_pm == "12":
            self.t = self.t + timedelta(hours=3)
        
         # AM中抜け(リアル時間のみ減算)
        rest = 0
  #      if self.sh_overtime != "1" and self.real_time > timedelta(hours=worktime):
  #          self.real_time = timedelta(hours=worktime + 1)
        # 休憩分を引く
        if self.t - timedelta(hours=rest) >= timedelta(hours=6):
            self.t = self.t - timedelta(hours=1)  # ６時間以上は休憩１時間を引く
            self.real_time = self.real_time - timedelta(hours=1)
        elif self.t - timedelta(hours=rest) >= timedelta(hours=5):
            self.t = self.t - timedelta(minutes=45)  # ５時間以上は休憩４５分を引く
            self.real_time = self.real_time - timedelta(minutes=45)
        
        # AMとPMは分ける。どっちも時間休を取るパターンがあるかもしれないので
        if self.sh_notification == "13":
            if self.t > timedelta(hours=worktime):
                if self.sh_overtime == "0":
                    self.real_time = timedelta(hours=worktime - 1)
                elif self.sh_overtime == "1":  # 残業した場合
                    self.real_time = self.real_time - timedelta(hours=1)
            else:
                self.real_time = self.real_time - timedelta(hours=1)
            
            rest = 1
        elif self.sh_notification == "14":
            if self.t > timedelta(hours=worktime):
                if self.sh_overtime == "0":
                    self.real_time = timedelta(hours=worktime - 2)
                elif self.sh_overtime == "1":  # 残業した場合
                    self.real_time = self.real_time - timedelta(hours=2)
            else:
                self.real_time = self.real_time - timedelta(hours=2)
            
            rest = 2
        elif self.sh_notification == "15":
            if self.t > timedelta(hours=worktime):
                if self.sh_overtime == "0":
                    self.real_time = timedelta(hours=worktime - 3)
                elif self.sh_overtime == "1":  # 残業した場合
                    self.real_time = self.real_time - timedelta(hours=3)
            else:
                self.real_time = self.real_time - timedelta(hours=3)
            
            rest = 3

        # PM中抜け(リアル時間のみ減算)
        if self.sh_notification_pm == "13":
            if self.t > timedelta(hours=worktime):
                if self.sh_overtime == "0":
                    self.real_time = timedelta(hours=worktime - 1)
                elif self.sh_overtime == "1":  # 残業した場合
                    self.real_time = self.real_time - timedelta(hours=1)
            else:
                self.real_time = self.real_time - timedelta(hours=1)
            
            rest = 1
        elif self.sh_notification_pm == "14":
            if self.t > timedelta(hours=worktime):
                if self.sh_overtime == "0":
                    self.real_time = timedelta(hours=worktime - 2)
                elif self.sh_overtime == "1":  # 残業した場合
                    self.real_time = self.real_time - timedelta(hours=2)
            else:
                self.real_time = self.real_time - timedelta(hours=2)
            
            rest = 2
        elif self.sh_notification_pm == "15":
            if self.t > timedelta(hours=worktime):
                if self.sh_overtime == "0":
                    self.real_time = timedelta(hours=worktime - 3)
                elif self.sh_overtime == "1":  # 残業した場合
                    self.real_time = self.real_time - timedelta(hours=3)
            else:
                self.real_time = self.real_time - timedelta(hours=3)
            
            rest = 3
         

        if self.sh_starttime != "00:00" and self.sh_endtime != "00:00":  # 欠勤・リフレッシュ休暇でなく打刻のある場合
                            
            if self.sh_notification != "3" and self.sh_notification != "4" and self.sh_notification != "5" and self.sh_notification != "6" and self.sh_notification != "16" and \
                self.sh_notification_pm != "4" and self.sh_notification_pm != "6" and self.sh_notification_pm != "16" and \
                    (self.sh_notification != "7" and self.sh_notification != "8" and self.sh_notification != "17" and \
                        self.sh_notification != "18" and self.sh_notification != "19" and self.sh_notification != "20"):

                        # パート以外(常勤)で契約時間を超えているか                        
                        if self.t > timedelta(hours=worktime): 
                            if self.sh_overtime == "0":
                                self.syukkin_times_0.append(worktime * 60 * 60)
                                if self.real_time > timedelta(hours=worktime):
                                    self.real_time_sum.append(worktime * 60 * 60)
                                else:
                                    self.real_time_sum.append(self.real_time.seconds)
                                # 祝日(2)、もしくはNSで土日(1)
                                if self.holiday == "2" or self.holiday == "1" and self.jobtype == 1 and self.u_contract_code == 2:
                                    self.syukkin_holiday_times_0.append(worktime * 60 * 60)
                                    #ここに
                            elif self.sh_overtime == "1":  # 残業した場合
                                self.syukkin_times_0.append(self.t.seconds)
                                self.real_time_sum.append(self.real_time.seconds)
                                self.over_time_0.append(self.t.seconds - worktime * 60 * 60)
                                if self.holiday == "2" or self.holiday == "1" and self.jobtype == 1 and self.u_contract_code == 2:
                                    self.syukkin_holiday_times_0.append(self.real_time.seconds)
                        else:
                            # 慶弔休暇の場合は有休扱い
                            if self.sh_notification == "9" or self.sh_notification_pm == "9":
                                self.syukkin_times_0.append(worktime * 60 * 60)
                                self.real_time_sum.append(worktime * 60 * 60)
                                
                            else:
                                self.syukkin_times_0.append(self.t.seconds)
                                self.real_time_sum.append(self.real_time.seconds)
                                if self.holiday == "2" or self.holiday == "1" and self.jobtype == 1 and self.u_contract_code == 2:
                                    self.syukkin_holiday_times_0.append(self.real_time.seconds)
                     
            # 半日出張、半休、生理休暇かつ打刻のある場合            
            elif self.sh_notification == "6" or self.sh_notification_pm == "6" or self.sh_notification == "4" or self.sh_notification == "16" or self.sh_notification_pm == "4" or self.sh_notification_pm == "16":  
                #8時間常勤もしくは32H常勤で有休と実働合わせて8H以上
                if (self.t + timedelta(hours=intHolidaytime / 2) > timedelta(hours=worktime)):
                    #残業申請なし
                    if self.sh_overtime == "0":
                        self.syukkin_times_0.append(worktime * 60 * 60)
                        self.real_time_sum.append(self.real_time.seconds)
                        if self.holiday == "2" or self.holiday == "1" and self.jobtype == 1 and self.u_contract_code == 2:
                            self.syukkin_holiday_times_0.append(worktime * 60 * 60)

                    elif self.sh_overtime == "1":  # 残業した場合
                        self.syukkin_times_0.append(self.t.seconds + worktime / 2 * 60 * 60)
                        self.over_time_0.append(self.t.seconds - worktime / 2 * 60 * 60)
                        self.real_time_sum.append(self.real_time.seconds)
                        if self.holiday == "2" or self.holiday == "1" and self.jobtype == 1 and self.u_contract_code == 2:
                            self.syukkin_holiday_times_0.append(self.real_time.seconds)
                # パート以外で1日の時間休以内の時間が入力されていた場合                                 
                elif (self.t + timedelta(hours=intHolidaytime) / 2) <= timedelta(hours=worktime):
                    self.syukkin_times_0.append(self.t.seconds + intHolidaytime / 2 * 60 * 60)
                    self.real_time_sum.append(self.real_time.seconds)
                    if self.holiday == "2" or self.holiday == "1" and self.jobtype == 1 and self.u_contract_code == 2:
                        self.syukkin_holiday_times_0.append(self.real_time.seconds)

            elif (self.sh_notification == "7" or self.sh_notification == "8" or self.sh_notification == "17" or \
                self.sh_notification == "18" or self.sh_notification == "19" or self.sh_notification == "20"):
                pass 
                    
        # 打刻は00:00で            
        elif self.sh_starttime == "00:00" and self.sh_endtime == "00:00":              
            # 全日年休、慶弔休暇の場合(有休)
            if self.sh_notification == "3" or self.sh_notification == "9":                        
                
                self.syukkin_times_0.append(intHolidaytime * 60 * 60)
            # 出張全日
            elif self.sh_notification == "5":    
                self.syukkin_times_0.append(worktime * 60 * 60)
            
            # 年休半日　or 生理休暇
            elif (self.sh_notification == "4" or self.sh_notification_pm == "4" or  \
                self.sh_notification == "16" or self.sh_notification_pm == "16"):
                self.syukkin_times_0.append(intHolidaytime / 2 * 60 * 60)
                
            
            # 出張半日
            elif (self.sh_notification == "6" or self.sh_notification_pm == "6"):
                
                self.syukkin_times_0.append(worktime / 2 * 60 * 60)
                                                                 

            elif (self.sh_notification == "7" or self.sh_notification == "8" or self.sh_notification == "17" or \
                self.sh_notification == "18" or self.sh_notification == "19" or self.sh_notification == "20"):
                pass                                                   
    

        


           


#***** パート職祝日用各勤怠時間計算ひな形 *****#
class PartCalcHolidayTimeClass:
    def __init__(self, t, sh_notification, sh_notification_pm, sh_starttime, sh_endtime, sh_overtime, u_contract_code,
                 syukkin_holiday_times_0, over_time_0, syukkin_times_0, rp_holiday_pw_time, rp_holiday_basetime_paidholiday):
        self.t = t
        self.sh_notification = sh_notification
        self.sh_notification_pm = sh_notification_pm
        self.sh_starttime = sh_starttime
        self.sh_endtime = sh_endtime
        self.sh_overtime = sh_overtime
        self.u_contract_code = u_contract_code
        self.syukkin_holiday_times_0 = syukkin_holiday_times_0
        self.over_time_0 = over_time_0
        self.syukkin_times_0 = syukkin_times_0
        self.rp_holiday_pw_time = rp_holiday_pw_time
        self.rp_holiday_basetime_paidholiday = rp_holiday_basetime_paidholiday

    def calc_hol_time(self):
        self.u_contract_code = 2
        if self.rp_holiday_pw_time != 0 and self.rp_holiday_basetime_paidholiday != 0:
            if self.sh_notification == "10":
                if self.sh_notification_pm == "10":
                    self.t = self.t + timedelta(hours=1) + timedelta(hours=1)
                elif self.sh_notification_pm == "11":
                    self.t = self.t + timedelta(hours=1) + timedelta(hours=2)
                elif self.sh_notification_pm == "12":
                    self.t = self.t + timedelta(hours=1) + timedelta(hours=3)
                elif self.sh_notification_pm == "13":
                    self.t = self.t + timedelta(hours=1) - timedelta(hours=1)
                elif self.sh_notification_pm == "14" and self.t >= timedelta(hours=1):
                    self.t = self.t + timedelta(hours=1) - timedelta(hours=2)
                elif self.sh_notification_pm == "15" and self.t >= timedelta(hours=2):
                    self.t = self.t + timedelta(hours=1) - timedelta(hours=3)
                else:
                    self.t = self.t + timedelta(hours=1)
            elif self.sh_notification == "11":
                if self.sh_notification_pm == "10":
                    self.t = self.t + timedelta(hours=2) + timedelta(hours=1)
                elif self.sh_notification_pm == "11":
                    self.t = self.t + timedelta(hours=2) + timedelta(hours=2)
                elif self.sh_notification_pm == "12":
                    self.t = self.t + timedelta(hours=2) + timedelta(hours=3)
                elif self.sh_notification_pm == "13":
                    self.t = self.t + timedelta(hours=2) - timedelta(hours=1)
                elif self.sh_notification_pm == "14":
                    self.t = self.t + timedelta(hours=2) - timedelta(hours=2)
                elif self.sh_notification_pm == "15" and self.t >= timedelta(hours=1):
                    self.t = self.t + timedelta(hours=2) - timedelta(hours=3)
                else:
                    self.t = self.t + timedelta(hours=2)
            elif self.sh_notification == "12":
                if self.sh_notification_pm == "10":
                    self.t = self.t + timedelta(hours=3) + timedelta(hours=1)
                elif self.sh_notification_pm == "11":
                    self.t = self.t + timedelta(hours=3) + timedelta(hours=2)
                elif self.sh_notification_pm == "12":
                    self.t = self.t + timedelta(hours=3) + timedelta(hours=3)
                elif self.sh_notification_pm == "13":
                    self.t = self.t + timedelta(hours=3) - timedelta(hours=1)
                elif self.sh_notification_pm == "14":
                    self.t = self.t + timedelta(hours=3) - timedelta(hours=2)
                elif self.sh_notification_pm == "15":
                    self.t = self.t + timedelta(hours=3) - timedelta(hours=3)
                else:
                    self.t = self.t + timedelta(hours=3)
            elif self.sh_notification == "13":
                if self.sh_notification_pm == "10":
                    self.t = self.t - timedelta(hours=1) + timedelta(hours=1)
                elif self.sh_notification_pm == "11":
                    self.t = self.t - timedelta(hours=1) + timedelta(hours=2)
                elif self.sh_notification_pm == "12":
                    self.t = self.t - timedelta(hours=1) + timedelta(hours=3)
                elif self.sh_notification_pm == "13" and self.t >= timedelta(hours=2):
                    self.t = self.t - timedelta(hours=1) - timedelta(hours=1)
                elif self.sh_notification_pm == "14" and self.t >= timedelta(hours=3):
                    self.t = self.t - timedelta(hours=1) - timedelta(hours=2)
                elif self.sh_notification_pm == "15" and self.t >= timedelta(hours=4):
                    self.t = self.t - timedelta(hours=1) - timedelta(hours=3)
                elif self.t >= 2:
                    self.t = self.t - timedelta(hours=1)
            elif self.sh_notification == "14":
                if self.sh_notification_pm == "10" and self.t >= timedelta(hours=2):
                    self.t = self.t - timedelta(hours=2) + timedelta(hours=1)
                elif self.sh_notification_pm == "11":
                    self.t = self.t - timedelta(hours=2) + timedelta(hours=2)
                elif self.sh_notification_pm == "12":
                    self.t = self.t - timedelta(hours=2) + timedelta(hours=3)
                elif self.sh_notification_pm == "13" and self.t >= timedelta(hours=3):
                    self.t = self.t - timedelta(hours=2) - timedelta(hours=1)
                elif self.sh_notification_pm == "14" and self.t >= timedelta(hours=4):
                    self.t = self.t - timedelta(hours=2) - timedelta(hours=2)
                elif self.sh_notification_pm == "15" and self.t >= timedelta(hours=5):
                    self.t = self.t - timedelta(hours=2) - timedelta(hours=3)
                elif self.t >= 3:
                    self.t = self.t - timedelta(hours=2)
            elif self.sh_notification == "15":
                if self.sh_notification_pm == "10" and self.t >= timedelta(hours=2):
                    self.t = self.t - timedelta(hours=3) + timedelta(hours=1)
                elif self.sh_notification_pm == "11" and self.t >= timedelta(hours=1):
                    self.t = self.t - timedelta(hours=3) + timedelta(hours=2)
                elif self.sh_notification_pm == "12":
                    self.t = self.t - timedelta(hours=3) + timedelta(hours=3)
                elif self.sh_notification_pm == "13" and self.t >= timedelta(hours=4):
                    self.t = self.t - timedelta(hours=3) - timedelta(hours=1)
                elif self.sh_notification_pm == "14" and self.t >= timedelta(hours=5):
                    self.t = self.t - timedelta(hours=3) - timedelta(hours=2)
                elif self.sh_notification_pm == "15" and self.t >= timedelta(hours=6):
                    self.t = self.t - timedelta(hours=3) - timedelta(hours=3)
                elif self.t >= 3:
                    self.t = self.t - timedelta(hours=3)
            elif self.sh_notification_pm == "10":
                self.t = self.t + timedelta(hours=1)
            elif self.sh_notification_pm == "11":
                self.t = self.t + timedelta(hours=2)
            elif self.sh_notification_pm == "12":
                self.t = self.t + timedelta(hours=3)
            elif self.sh_notification_pm == "13" and self.t >= timedelta(hours=1):
                self.t = self.t - timedelta(hours=1)
            elif self.sh_notification_pm == "14" and self.t >= timedelta(hours=2):
                self.t = self.t - timedelta(hours=2)
            elif self.sh_notification_pm == "15" and self.t >= timedelta(hours=3):
                self.t = self.t - timedelta(hours=3)
            else:
                self.t = self.t

            if self.t >= timedelta(hours=6):
                self.t = self.t - timedelta(hours=1)  # ６時間以上は休憩１時間を引く
            elif self.t >= timedelta(hours=5):
                self.t = self.t - timedelta(minutes=45)  # ５時間以上は休憩４５分を引く


            if self.sh_starttime != "00:00" and self.sh_endtime != "00:00":  # 欠勤・リフレッシュ休暇でなく打刻のある場合
                                
                if self.sh_notification != "3" and self.sh_notification != "4" and self.sh_notification != "5" and self.sh_notification != "6" and self.sh_notification != "16" and \
                    self.sh_notification_pm != "4" and self.sh_notification_pm != "6" and self.sh_notification_pm != "16" and \
                        self.sh_notification != "7" and self.sh_notification != "8" and self.sh_notification != "17" and \
                            self.sh_notification != "18" and self.sh_notification != "19" and self.sh_notification != "20":
                            
                                if self.u_contract_code == 2 and self.t > timedelta(hours=self.rp_holiday_pw_time): 
                                    if self.sh_overtime == "0":
                                        self.syukkin_times_0.append(self.rp_holiday_pw_time * 60 * 60)
                                        self.syukkin_holiday_times_0.append(self.rp_holiday_pw_time * 60 * 60)
                                                                
                                    elif self.sh_overtime == "1":  # 残業した場合
                                        self.syukkin_times_0.append(self.t.seconds)
                                        self.syukkin_holiday_times_0.append(self.t.seconds)
                                        self.over_time_0.append(self.t.seconds - self.rp_holiday_pw_time * 60 * 60)

                                else:
                                    self.syukkin_times_0.append(self.t.seconds)
                                    self.syukkin_holiday_times_0.append(self.t.seconds)

                elif self.sh_notification == "6" or self.sh_notification_pm == "6":  # （半日）かつ打刻のある場合
                    if self.u_contract_code == 2 and (self.t + timedelta(hours=self.rp_holiday_pw_time) / 2) > timedelta(hours=self.rp_holiday_pw_time):
                        if self.sh_overtime == "0":
                            self.syukkin_times_0.append(self.rp_holiday_pw_time * 60 * 60)
                            self.syukkin_holiday_times_0.append(self.rp_holiday_pw_time * 60 * 60)
                        elif self.sh_overtime == "1":  # 残業した場合
                            self.syukkin_times_0.append(self.t.seconds + (self.rp_holiday_pw_time / 2) * 60 * 60)
                            self.syukkin_holiday_times_0.append(self.t.seconds + (self.rp_holiday_pw_time / 2) * 60 * 60)
                            self.over_time_0.append(self.t.seconds + (self.rp_holiday_pw_time / 2) * 60 * 60 - self.rp_holiday_pw_time * 60 * 60)                            
                    elif self.u_contract_code == 2 and (self.t + timedelta(hours=self.rp_holiday_pw_time) / 2) <= timedelta(hours=self.rp_holiday_pw_time):
                        self.syukkin_times_0.append(self.t.seconds + (self.rp_holiday_pw_time) / 2 * 60 * 60)
                        self.syukkin_holiday_times_0.append(self.t.seconds + (self.rp_holiday_pw_time) / 2 * 60 * 60)

                elif self.sh_notification == "4" or self.sh_notification == "16" or self.sh_notification_pm == "4" or self.sh_notification_pm == "16":  # （半日）かつ打刻のある場合
                    if self.u_contract_code == 2 and (self.t + timedelta(hours=self.rp_holiday_basetime_paidholiday) / 2) > timedelta(hours=self.rp_holiday_pw_time):
                        if self.sh_overtime == "0":
                            self.syukkin_times_0.append(self.rp_holiday_pw_time * 60 * 60)
                            
                            #self.syukkin_holiday_times_0.append(self.rp_holiday_pw_time * 60 * 60)
                            self.syukkin_holiday_times_0.append(self.t.seconds)
                        
                        elif self.sh_overtime == "1":  # 残業した場合
                            self.syukkin_times_0.append(self.t.seconds + (self.rp_holiday_basetime_paidholiday / 2) * 60 * 60)
                            
                            #self.syukkin_holiday_times_0.append(self.t.seconds + (self.rp_holiday_basetime_paidholiday / 2) * 60 * 60)
                            self.syukkin_holiday_times_0.append(self.t.seconds)
                            
                            self.over_time_0.append(self.t.seconds + (self.rp_holiday_basetime_paidholiday / 2) * 60 * 60 - self.rp_holiday_pw_time * 60 * 60)                            
                    elif self.u_contract_code == 2 and (self.t + timedelta(hours=self.rp_holiday_basetime_paidholiday) / 2) <= timedelta(hours=self.rp_holiday_pw_time):
                        self.syukkin_times_0.append(self.t.seconds + (self.rp_holiday_basetime_paidholiday) / 2 * 60 * 60)                    
                        
                        #self.syukkin_holiday_times_0.append(self.t.seconds + (self.rp_holiday_basetime_paidholiday) / 2 * 60 * 60)                             
                        self.syukkin_holiday_times_0.append(self.t.seconds)

                    
                elif (self.sh_notification == "7" or self.sh_notification == "8" or self.sh_notification == "17" or \
                    self.sh_notification == "18" or self.sh_notification == "19" or self.sh_notification == "20"):
                    pass                        

                        
            elif self.sh_starttime == "00:00" and self.sh_endtime == "00:00":
                if self.sh_notification == "3":                        
                    if self.u_contract_code == 2: 
                        self.syukkin_times_0.append(self.rp_holiday_basetime_paidholiday * 60 * 60)
                        #self.syukkin_holiday_times_0.append(self.rp_holiday_basetime_paidholiday * 60 * 60)
                elif self.sh_notification == "5":
                    if self.u_contract_code == 2:
                        self.syukkin_times_0.append(self.rp_holiday_pw_time * 60 * 60)
                        #self.syukkin_holiday_times_0.append(self.rp_holiday_pw_time * 60 * 60)                    
                elif (self.sh_notification == "6" or self.sh_notification_pm == "6"):
                    if self.u_contract_code == 2:
                        self.syukkin_times_0.append((self.rp_holiday_pw_time / 2) * 60 * 60)
                        #self.syukkin_holiday_times_0.append((self.rp_holiday_pw_time / 2) * 60 * 60)
                elif (self.sh_notification == "4" or self.sh_notification_pm == "4" or self.sh_notification == "16" or \
                    self.sh_notification_pm == "16"):
                    if self.u_contract_code == 2: 
                        self.syukkin_times_0.append((self.rp_holiday_basetime_paidholiday / 2) * 60 * 60)
                        #self.syukkin_holiday_times_0.append((self.rp_holiday_basetime_paidholiday / 2) * 60 * 60)
                        
                elif (self.sh_notification == "7" or self.sh_notification == "8" or self.sh_notification == "17" or \
                    self.sh_notification == "18" or self.sh_notification == "19" or self.sh_notification == "20"):
                    pass    


#************************************** 時間休カウント ********************************************#
class TimeOffClass:
    def __init__(self, y, m, d, sh_workday, sh_notification, sh_notification_pm, timeoff1, timeoff2, timeoff3, halfway_through1, 
                 halfway_through2, halfway_through3):
        self.y = y
        self.m = m
        self.d = d
        self.sh_workday = sh_workday
        self.sh_notification = sh_notification
        self.sh_notification_pm = sh_notification_pm
        self.timeoff1 = timeoff1
        self.timeoff2 = timeoff2
        self.timeoff3 = timeoff3
        self.halfway_through1 = halfway_through1
        self.halfway_through2 = halfway_through2
        self.halfway_through3 = halfway_through3
        
    def cnt_time_off(self):
        if datetime(self.y, self.m, 1) <= datetime.strptime(self.sh_workday, '%Y-%m-%d') and \
            datetime(self.y, self.m, self.d) >= datetime.strptime(self.sh_workday, '%Y-%m-%d'):                                                
                if self.sh_notification == "10" or self.sh_notification_pm == "10":
                    self.timeoff1.append("cnt1")
                if self.sh_notification == "11" or self.sh_notification_pm == "11":
                    self.timeoff2.append("cnt2")
                if self.sh_notification == "12" or self.sh_notification_pm == "12":
                    self.timeoff3.append("cnt3")
                if self.sh_notification == "13" or self.sh_notification_pm == "13":
                    self.halfway_through1.append("cnt01")
                if self.sh_notification == "14" or self.sh_notification_pm == "14":
                    self.halfway_through2.append("cnt02")
                if self.sh_notification == "15" or self.sh_notification_pm == "15":
                    self.halfway_through3.append("cnt03")