import pytest

import sys
# sys.path.append(os.path.abspath(".."))
import pathlib


packagedir = pathlib.Path(__file__).resolve().parent.parent.parent
print(packagedir)
sys.path.append(str(packagedir))

from app import db, app

"""
  https://stackoverflow.com/questions/31444036/runtimeerror-working-outside-of-application-context
  """
@pytest.fixture
def app_context():
  with app.app_context():
    db.create_all()
    yield
