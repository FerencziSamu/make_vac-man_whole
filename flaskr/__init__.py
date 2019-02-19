import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail

# create and configure the app
app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.from_mapping(
    SECRET_KEY='dev',
    SQLALCHEMY_DATABASE_URI='sqlite:///site.db'
)

db = SQLAlchemy(app)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = app.config.get('USER_EMAIL')
app.config['MAIL_PASSWORD'] = app.config.get('USER_PW')
mail = Mail(app)

from flaskr import routes

# ensure the instance and reports folder exists
try:
    os.makedirs("flaskr/" + app.instance_path)
except OSError:
    pass

try:
    os.mkdir("flaskr/reports", 0o777)
except OSError:
    pass
