from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

import config

engine = create_engine(config.DB_URL, encoding = "utf-8", echo = config.DB_DEBUG_ECHO)
Base = declarative_base()

class HelloWorld(Base):
  __tablename__ = "hello_world"

  id = Column(Integer, primary_key=True)
  name = Column(String)

  def __repr__(self):
    return "HelloWorld(%d, %s)" % (self.id, self.name)


def create_schema():
  Base.metadata.create_all(engine) 

def delete_schema():
  Base.metadata.drop_all(engine) 

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



