from flask import Flask

app = Flask(__name__)

import logging
from logging.handlers import RotatingFileHandler
file_handler = RotatingFileHandler("logs/ozaur.log")
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)

