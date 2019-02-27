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

