from flask import render_template, redirect, request
from flask_login import current_user
from flask_login.utils import login_required
from flask.helpers import url_for

from app import app, db

from marshmallow import Schema, fields, post_load

class ModelDummy():
  def __init__(self, comment) -> None:
    self.comment = comment

class DummySchema(Schema):
  comment = fields.Str(require=True)

  @post_load
  def build(self, data, **kwargs):
    return ModelDummy(**data)

@app.route('/dummy/<target_id>', methods=['GET', 'POST'])
@login_required
def appear_sub(target_id):
  # if request.method == 'GET':
    return render_template('admin/dummy.html',
                           t_num=target_id, stf_login=current_user)

  # 10月27日追加
  # dummyデータ受取
  # response = {}
  # if request.method == 'POST':
@app.route('/dummy/display', methods=['POST'])
@login_required
def appear_json():
  schema = DummySchema()
  response: dict = request.json['comment']
  resp_data = ModelDummy(comment=response)
  json_data = schema.dump(resp_data)

  # return json_data
  return render_template('admin/edit_data_user.html', res=json_data, stf_login=current_user)
