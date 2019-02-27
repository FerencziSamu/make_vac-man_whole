import pytest
# import os
# import tempfile
from flaskr import app as application
from flaskr import routes


@pytest.fixture(scope='session')
def app():
    app = application
    app.config['TESTING'] = True
    yield app


@pytest.fixture(scope='session')
def client(app):
    app.app_context()
    with app.test_client() as client:
        yield client





# @pytest.fixture
# def client():
#     app = application
#     db_fd, app.config['DATABASE'] = tempfile.mkstemp()
#     app.config['TESTING'] = True
#     client = app.test_client()
#
#     with app.app_context():
#         app.init_db()
#
#     yield client
#
#     os.close(db_fd)
#     os.unlink(app.config['DATABASE'])
