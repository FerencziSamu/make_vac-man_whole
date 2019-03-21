import os
import tempfile
import pytest

from flaskr.db import init_db
from flaskr import app as application


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
