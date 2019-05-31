import os
import logging

from flask import Flask, jsonify
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy

# create and configure the app
app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.from_mapping(
    SECRET_KEY='dev',
    SQLALCHEMY_DATABASE_URI='sqlite:///site.db'
)
logging.basicConfig(filename='flaskr_log.log', format='%(asctime)s - %(message)s', level=logging.NOTSET)
db = SQLAlchemy(app)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = app.config.get('USER_EMAIL')
app.config['MAIL_PASSWORD'] = app.config.get('USER_PW')
mail = Mail(app)


@app.errorhandler(Exception)
def handle_invalid_usage(error):
    response = jsonify({'message': 'Internal server error', 'description': str(error)})
    response.status_code = 500
    logging.exception(response)
    return response


from flaskr import routes

# ensure the instance and reports folder exists
try:
    os.makedirs(app.instance_path)
except FileExistsError as e:
    logging.error("\n\n\n" + "Error: " + str(e))

try:
    os.mkdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "reports"), 0o777)
except FileExistsError as e:
    logging.error("Error: " + str(e))
