from flask import render_template

from app import app
from app import login_require

from models_aprv import NotificationList

@app.route('/approval-list/<STAFFID>', methods=['GET'])
@login_require
def get_approval_list(STAFFID):
    notification_list: NotificationList = NotificationList.query(NotificationList.STAFFID == STAFFID).all()
    # return notification_list
    return render_template('notification_list.html', notice_list=notification_list)