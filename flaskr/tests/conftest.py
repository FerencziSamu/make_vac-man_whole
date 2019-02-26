import pytest
from flaskr import app as application


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

