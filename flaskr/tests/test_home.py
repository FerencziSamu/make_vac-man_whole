def test_home_1(client):
    resp = client.get('/')
    assert resp.status_code == 200


def test_home_2(client):
    resp = client.get('/')
    assert resp.content_type == "text/html; charset=utf-8"


def test_home_3(client):
    resp = client.get('/')
    assert b"Logout" not in resp.data


def test_home_4(client):
    resp = client.get('/')
    assert b"Login" in resp.data


def test_logout_1(client):
    with client.session_transaction() as session:
        session['user'] = "test_session_user"
    resp = client.get('/logout', follow_redirects=True)
    assert b"Welcome! Please log in!" in resp.data
    assert resp.status_code == 200
    assert session['user'] is None

