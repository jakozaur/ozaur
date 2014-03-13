from flask import Flask
import config

app = Flask(__name__)

app.secret_key = config.SECRET_KEY

import logging
from logging import Formatter, getLogger
from logging.handlers import RotatingFileHandler


for logger, name in [(app.logger, "ozaur"), (getLogger("sqlalchemy"), "sql"), (getLogger("werkzeug"), "werkzeug")]:
  file_handler = RotatingFileHandler("logs/%s.log" % (name))
  file_handler.setLevel(logging.INFO)
  formatter = '%(asctime)s %(levelname)s: %(message)s '
  if name == "ozaur":
    formatter += '[in %(pathname)s:%(lineno)d]'
  file_handler.setFormatter(Formatter(formatter))
  logger.setLevel(logging.INFO)
  logger.addHandler(file_handler)

