''' ivrhub
a flask skeleton
'''
import datetime
from logging import (handlers, Formatter)

from flask import Flask
from flaskext.bcrypt import Bcrypt
from mongoengine import *


app = Flask(__name__)
app.config.from_envvar('IVRHUB_SETTINGS')
bcrypt = Bcrypt(app)


# attach the file logger
if not app.config['TESTING']:
    file_handler = handlers.RotatingFileHandler(app.config['LOG_FILE'])
    file_handler.setLevel(app.config['LOG_LEVEL'])
    file_handler.setFormatter(Formatter(
        '%(asctime)s %(levelname)s: %(message)s'
    ))
    app.logger.addHandler(file_handler)


# initialize the mongoengine connection
connect(app.config['MONGO_CONFIG']['db_name']
    , host=app.config['MONGO_CONFIG']['host']
    , port=int(app.config['MONGO_CONFIG']['port'])
)


import ivrhub.views
