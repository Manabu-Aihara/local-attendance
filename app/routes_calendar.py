import calendar
import json

from flask import render_template, redirect, request
from flask_login import current_user
from flask_login.utils import login_required

from app import app, db

from app.models_tt import TodoOrm

@app.after_request
def after_request(response):
    allowed_origins = ['http://localhost:5173']
    origin = request.headers.get('Origin')
    if origin in allowed_origins:
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Headers', 'Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

cssclasses = ["sun red", "mon", "tue", "wed", "thu", "fri", "sat blue"]

calendar.setfirstweekday(calendar.SUNDAY)
class CustomHTMLCal(calendar.HTMLCalendar):
    cssclasses = [style + " text-nowrap" for style in
                calendar.HTMLCalendar.cssclasses]
    cssclass_month_head = "text-center month-head"
    cssclass_month = "text-center month"
    cssclass_year = "text-italic lead"
    def __init__(self, firstweekday: int = 0) -> None:
        super().__init__(firstweekday = 6)
    
@app.route('/month', methods=['GET'])
@login_required
def diplay_calendar():
	html_calendar = CustomHTMLCal()
	fm_month = html_calendar.formatmonth(2023, 9)

	return render_template('attendance/month_calendar.html',
                        html_cal=fm_month,
                        stf_login=current_user)

@app.route('/todo/add', methods=['POST'])
@login_required
def append_todo(summary: str, owner: str):
     one_todo = TodoOrm(summary, owner)
     db.session.add(one_todo)
     db.session.commit()

@app.route('/todo/all', methods=['GET'])
@login_required
def print_all():
     data = TodoOrm.query.all()
     return json.dump(data)
