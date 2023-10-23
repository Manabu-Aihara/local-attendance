import calendar
import json
from bson.json_util import dumps

from flask import Flask, render_template, request, redirect
from flask_login import current_user
from flask_login.utils import login_required
from flask_cors import CORS
# from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
# from flask_login import LoginManager

# from config import Config
from app import app, db
from app.models_tt import TodoOrm, TodoModelSchema

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

# app = Flask(__name__)
# app.config.from_object(Config)
CORS(app)
# @app.after_request
# def after_request(response):
#     allowed_origins = ['http://localhost:5173']
#     origin = request.headers.get('Origin')
#     if origin in allowed_origins:
#         response.headers.add('Access-Control-Allow-Origin', origin)
#         response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
#         response.headers.add('Access-Control-Allow-Headers', 'Authorization')
#         response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
#         response.headers.add('Access-Control-Allow-Credentials', 'true')
#     return response
# db = SQLAlchemy(app)
# Migrate(app, db)
# LoginManager(app)

@app.route('/todo/add', methods=['POST'])
# @login_required
def append_todo():
	schema = TodoModelSchema()
	summary = request.json['summary']
	owner = request.json['owner']
	one_todo = TodoOrm(summary=summary, owner=owner)
	db.session.add(one_todo)
	db.session.commit()

	return redirect('/todo/all')

@app.route('/todo/all', methods=['GET'])
# @login_required
def print_all():
	schema = TodoModelSchema()
	todos = TodoOrm.query.order_by(TodoOrm.id).all()
	list_data = []
	for todo in todos:
		# dict_data = dict(todo)
		list_data.append(schema.dump(todo))
	return list_data
