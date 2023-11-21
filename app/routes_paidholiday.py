from flask import render_template
from flask_login import current_user
from flask_login.utils import login_required

from app import app
from app.holiday_acquisition import HolidayAcquire


# 個別申請リストページ
@app.route("/notification-list/<STAFFID>", methods=["GET"])
@login_required
def get_notification_list(STAFFID):
    # paid_holiday_list = PaidHoliday(STAFFID)

    holidays_print_obj = HolidayAcquire(STAFFID)
    start_and_holiday = holidays_print_obj.plus_next_holidays()

    return render_template(
        "attendance/notification_list.html",
        holiday_info=start_and_holiday.items(),
        stf_login=current_user,
    )
