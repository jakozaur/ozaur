from sqlalchemy import create_engine, Column, Integer, String, Index, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from flask.ext.login import UserMixin
from flask.ext.sqlalchemy import SQLAlchemy

from main import app
import config

app.config["SQLALCHEMY_DATABASE_URI"] = config.DB_URL
app.config["SQLALCHEMY_ECHO"] = config.DB_DEBUG_ECHO

db = SQLAlchemy(app)

class User(db.Model, UserMixin):
  __tablename__ = "user"

  id = Column(Integer, primary_key=True, autoincrement=True)
  email = Column(String(256), nullable=False)
  display_name = Column(String(64), nullable=False)
  headline = Column(String(128), nullable=False)
  industry = Column(String(64), nullable=False)
  location = Column(String(64), nullable=False)
  interested_in = Column(String(256), nullable=False)
  photo_url = Column(String(256))

  __table_args__ = (Index("user_email_idx", "email", unique=True),)

class Profile(db.Model):
  __tablename__ = "profile"

  id = Column(Integer, primary_key=True, autoincrement=True)
  user_id = Column(Integer, ForeignKey("user.id"), nullable=False)

  external_key = Column(String(128))
  data_json = Column(Text)

  user = relationship("User", backref="profiles")

def create_schema():
  db.create_all()

def delete_schema():
  db.drop_all()

if __name__ == '__main__':
  from sys import argv
  if len(argv) != 2 or argv[1] not in ["create", "delete"]:
    print "Invalid argument"
    print "Please use %s create|delete" % (argv[0])
  else:
    if argv[1] == "create":
      print "Creating DB schema"
      create_schema()
    elif argv[1] == "delete":
      print "Deleting all DB tables"
      delete_schema()



