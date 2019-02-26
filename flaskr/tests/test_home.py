def test_home_1(client):
    resp = client.get('/')
    assert resp.status_code == 200
