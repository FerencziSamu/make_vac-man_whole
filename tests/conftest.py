import os
import tempfile
import pytest

from flaskr.db import init_db
from flaskr import app as application, logging


# @pytest.fixture(scope='session')
# def app():
#     app = application
#     db_fd, app.config['DATABASE'] = tempfile.mkstemp()
#     app.config['TESTING'] = True
#     yield app
#     os.close(db_fd)
#     os.unlink(app.config['DATABASE'])
#
#
# @pytest.fixture(scope='session')
# def client(app):
#     app.app_context()
#     with app.test_client() as client:
#         app.init_db()
#         yield client


@pytest.fixture
def client():
    app = application
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['SECRET_KEY'] = 'sekrit!'
    app.config['TESTING'] = True

    client = app.test_client()

    with app.app_context():
        init_db()

    yield client

    os.close(db_fd)
    os.unlink(app.config['DATABASE'])
