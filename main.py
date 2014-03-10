from flask import Flask

app = Flask(__name__)

import logging
from logging import Formatter
from logging.handlers import RotatingFileHandler
file_handler = RotatingFileHandler("logs/ozaur.log")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(Formatter(
  '%(asctime)s %(levelname)s: %(message)s '
  '[in %(pathname)s:%(lineno)d]'
))

app.logger.addHandler(file_handler)

