from flask import render_template, redirect
from flask_login import current_user
from flask_login.utils import login_required
from flask.helpers import url_for

from app import app
from app.models import User, StaffLoggin
from app.models_aprv import NotificationList

def stuff_login_confirm(func):
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        else:
            effective_user: StaffLoggin = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
        return func(effective_user)
    return wrapper

@app.route('/approval-list/<STAFFID>', methods=['GET'])
@login_required
# @stuff_login_confirm
def get_approval_list(STAFFID):
    # principal_user = User.query.get(STAFFID)
    """
        これが無いとページ遷移不可
    """
    effective_user = StaffLoggin.query.filter_by(STAFFID=current_user.STAFFID).first()
    notification_list = NotificationList.query.get(STAFFID)
    return render_template('attendance/notification_list.html', nlst=notification_list, stf_login=effective_user)