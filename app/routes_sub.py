from flask import render_template, redirect, request
from flask_login import current_user
from flask_login.utils import login_required
from flask.helpers import url_for

from app import app, db

@app.route('/dummy/<target_id>', methods=['GET', 'POST'])
@login_required
def action_sub(target_id):
  if request.method == 'GET':
    return render_template('admin/dummy.html',
                           t_num=target_id, stf_login=current_user)

  # elif request.method == 'POST':
