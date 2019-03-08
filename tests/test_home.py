from flaskr import app


# Checks the response from the index page
def test_home_1(client):
    resp = client.get('/')
    assert resp.status_code == 200
    assert b"Welcome! Please log in!" in resp.data
    assert resp.content_type == "text/html; charset=utf-8"
    assert b"Logout" not in resp.data


# AssertionError: Popped wrong request context.
# def test_logout_1():
#     with app.test_client() as c:
#         with c.session_transaction() as sess:
#             sess['user'] = "user_test_1"
#             with app.test_request_context():
#                 assert sess['user'] == "user_test_1"
#                 resp = c.get('/logout', follow_redirects=False)
#                 assert b"Welcome! Please log in!" in resp.data
#                 assert resp.status_code == 200


# Once called, sends random user name and password to the authorized page
def login(client, username, password):
    return client.post('/login/authorized', data=dict(
        username=username,
        password=password
    ), follow_redirects=True)


# Checks if we click on "login" it starts to redirect us
def test_login_1(client):
    resp = client.get('/login', follow_redirects=False)
    assert b"redirect" in resp.data


# Checks the redirection from login page to the Google authorization site
def test_login_2(client):
    from flask import url_for
    app.config['SERVER_NAME'] = "{rv}.localdomain"
    with app.app_context():
        response = client.get(url_for('login'), follow_redirects=False)
        # check if the path changed
        assert b"https://accounts.google.com" in response.data


# Checks if we can force a login from outside of authorization
def test_login_3(client):
    rv = login(client, "Username", "Password")
    assert b'The method is not allowed for the requested URL.' in rv.data


# Logout redirected us  to the main page
'''<class 'werkzeug.local.LocalProxy'> instead of session_transaction() object,
read more:http://flask.pocoo.org/docs/1.0/testing/'''
def test_logout_1():
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess["user"] = "test_session_user"
        resp = c.get('/logout', follow_redirects=True)
        assert b"Welcome! Please log in!" in resp.data
        assert resp.status_code == 200

