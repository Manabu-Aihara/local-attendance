from typing import Optional
# from sqlalchemy import Column, Integer, String, Boolean
from flask_sqlalchemy.model import DefaultMeta
from pydantic import BaseModel, constr, ConfigDict

from app import db

BaseMeta: DefaultMeta = db.Model

class TodoOrm(BaseMeta):
	__tablename__ = "T_TODO"

	id = db.Column(db.Integer, primary_key=True, index=True, autoincrement=True)
	summary = db.Column(db.String(50), index=True, nullable=False)
	owner = db.Column(db.String(20), index=True, nullable=False)
	done = db.Column(db.Boolean, index=True, nullable=False, default=False)

	def __init__(self, summary, owner):
		self.summary = summary
		self.owner = owner

	# def __repr__(self):
	#       return f'{{id: {self.id}, summary: {self.summary}, owner: {self.owner}, done: {self.done}}}'
	# return f'{self.id}, {self.summary}, {self.owner}, {self.done}'

class TodoTypeModel(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	# id: int
	summary: Optional[constr(max_length=50)]
	owner: Optional[constr(max_length=20)]
	# done: bool

	# class Config:
	#   orm_mode = True
	# モデルインスタンスを作るためにfrom_ormというコンストラクタを使用すること

class AllArgConstructorModel:

	def __init__(self, **kwargs):
		for k, v in kwargs.items():
			setattr(self, k, v)

class TodoModel(AllArgConstructorModel):
	pass
        
from marshmallow import Schema, fields, post_load

class TodoModelSchema(Schema):
	id = fields.Int(required=True)
	summary = fields.Str(required=True)
	owner = fields.Str(required=True)
	done = fields.Boolean(required=True)

	@post_load
	def build(self, data, **kwargs):
		return TodoOrm(**data)
	