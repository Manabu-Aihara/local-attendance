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

class TodoModel(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  # id: int
  summary: Optional[constr(max_length=50)]
  owner: Optional[constr(max_length=20)]
  # done: bool

  # class Config:
  #   orm_mode = True
  # モデルインスタンスを作るためにfrom_ormというコンストラクタを使用すること

