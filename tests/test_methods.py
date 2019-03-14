from unittest import mock
from flask_mail import Message
from flaskr import routes, app, logging
import pytest, datetime


# Deleting all data from db before testing
routes.db.session.query(routes.User).delete()
routes.db.session.query(routes.LeaveRequest).delete()
routes.db.session.query(routes.LeaveCategory).delete()
routes.db.session.commit()

# Global variable for db calling

db = routes.db.session


# Method to delete everything from DB
def delete_everything_from_db():
    db.query(routes.LeaveCategory).delete()
    db.query(routes.LeaveRequest).delete()
    db.query(routes.User).delete()
    db.commit()


# Checks the response from the index page
def test_home_1(client):
    resp = client.get('/')
    assert resp.status_code == 200
    assert b"Welcome! Please log in!" in resp.data
    assert resp.content_type == "text/html; charset=utf-8"
    assert b"Logout" not in resp.data


# Checks if the user is in the session and it is an administrator
def test_home_2(mocker):
    class MockedUserInfo:
        def __init__(self, userinfo):
            self.data = userinfo

    try:
        routes.create_default_cat()
        fake_user = routes.User(email="test_elek@invenshure.com", user_group="administrator", days=0,
                                notification=0,
                                leave_category_id=1)
        db.add(fake_user)
        db.commit()

        json_data = {
            "id": "101843067871304637814",
            "email": "test_elek@invenshure.com",
            "verified_email": "True",
            "picture": "aaaaaaaaaa.jpeg",
            "hd": "invenshure.com"
        }

        with app.test_client() as client:
            mocker.patch('flaskr.routes.google.get', return_value=MockedUserInfo(json_data))
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.get('/')
            assert resp.status_code == 200
            assert b"Home" in resp.data
            assert b"Admin" in resp.data
            assert b"Leave Requests" in resp.data
    finally:
        delete_everything_from_db()


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


# Logout redirected us to the main page
'''<class 'werkzeug.local.LocalProxy'> instead of session_transaction() object,
read more:http://flask.pocoo.org/docs/1.0/testing/'''
def test_logout_1():
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess["user"] = "test_session_user"
        resp = c.get('/logout', follow_redirects=True)
        assert b"Welcome! Please log in!" in resp.data
        assert resp.status_code == 200


def test_create_end_date():
    routes.create_end_date(['01', '15', '2019'])
    # With invalid character
    with pytest.raises(ValueError):
        routes.create_end_date(['01', 'X', '2019'])
    # With none character
    with pytest.raises(ValueError):
        routes.create_end_date(['01', '', '2019'])
    # With less character then expected
    with pytest.raises(IndexError):
        routes.create_end_date(['01', '2019'])
    # With wrong order
    with pytest.raises(ValueError):
        routes.create_end_date(['2019', '01', '15'])
    # With invalid values
    with pytest.raises(ValueError):
        routes.create_end_date(['00', '00', '0000'])


def test_create_start_date():
    routes.create_start_date(['01', '15', '2019'])
    # With invalid character
    with pytest.raises(ValueError):
        routes.create_start_date(['01', 'X', '2019'])
    # With none character
    with pytest.raises(ValueError):
        routes.create_start_date(['01', '', '2019'])
    # With less character then expected
    with pytest.raises(IndexError):
        routes.create_start_date(['01', '2019'])
    # With wrong order
    with pytest.raises(ValueError):
        routes.create_start_date(['2019', '01', '15'])
    # With invalid values
    with pytest.raises(ValueError):
        routes.create_start_date(['00', '00', '0000'])


def test_send_email():
    routes.send_email("testemail", email=None)
    # With invalid email address
    with pytest.raises(AttributeError):
        routes.send_email("testemail", email="random@random.com")
    # With wrong email address
    with pytest.raises(AttributeError):
        routes.send_email("testemail", email=12345)
    # With email address what is not in the database
    with pytest.raises(AttributeError):
        routes.send_email("testemail", email="random@gmail.com")


# With no recipients
def test_send_async_email_1():
    msg = Message('Vacation Management',
                  sender='noreply@demo.com',
                  recipients=None)
    msg.body = "test_email"
    routes.send_async_email(msg)


# With 2 recipients in db. The settings does not matter, check logic! If user in db has been added to recipients, email
# is about to be sent
def test_send_async_email_2():
    msg = Message('Vacation Management',
                  sender='noreply@demo.com',
                  recipients=['samuelferenczi@invenshure.com', 'huli.opaltest@gmail.com'])
    msg.body = "test_email"
    routes.send_async_email(msg)


# With invalid recipient, warns test_send_async_email_3 never awaited, hence turned off
@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore:")
async def test_send_async_email_3():
    msg = Message('Vacation Management',
                  sender='noreply@demo.com',
                  recipients=12345)
    msg.body = "test_email"
    routes.send_async_email(msg)


# With invalid sender, warns test_send_async_email_4 never awaited, hence turned off
@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore:")
async def test_send_async_email_4():
    msg = Message('Vacation Management',
                  sender=12345,
                  recipients="samuelferenczi@invenshure.com")
    msg.body = "test_email"
    routes.send_async_email(msg)


# With empty sender&recipients, warns test_send_async_email_5 never awaited, hence turned off
@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore:")
async def test_send_async_email_5():
    msg = Message('Vacation Management',
                  sender="",
                  recipients="")
    msg.body = "test_email"
    routes.send_async_email(msg)


# Without first parameter, warns test_send_async_email_6 never awaited, hence turned off
@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore:")
async def test_send_async_email_6():
    msg = Message(sender='noreply@demo.com', recipients="samuelferenczi@invenshure.com")
    msg.body = "test_email"
    routes.send_async_email(msg)


# Without integer body, warns test_send_async_email_7 never awaited, hence turned off
@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore:")
async def test_send_async_email_7():
    msg = Message('Vacation Management',
                  sender='noreply@demo.com',
                  recipients="samuelferenczi@invenshure.com")
    msg.body = 12345
    routes.send_async_email(msg)


# With 2 recipients, but only 1 in db. Only that one receives the email, warns test_send_async_email_8
# never awaited, hence turned off
@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore:")
async def test_send_async_email_8():
    msg = Message('Vacation Management',
                  sender='noreply@demo.com',
                  recipients=['samuelferenczi@invenshure.com', 'samu.ferenczi@gmail.com'])
    msg.body = "test_email"
    routes.send_async_email(msg)


def test_get_leavecategory():
    try:
        fake_category = routes.LeaveCategory(category="test_test_0", max_days=20)
        db.add(fake_category)
        db.commit()
        # With correct mapping
        q = routes.get_leave_category(field={'id': fake_category.id})
        assert isinstance(q, routes.LeaveCategory)
        # Without mapping
        with pytest.raises(TypeError):
            routes.get_leave_category(field=None)
        # With empty mapping
        q = routes.get_leave_category(field={'': ''})
        assert q is None
        # 'LeaveCategory' has no attribute 'asd'
        q = routes.get_leave_category(field={'asd': 1})
        assert q is None
        # 'LeaveCategory' has no property 'asd'
        q = routes.get_leave_category(field={'id': 'asd'})
        assert q is None
    finally:
        fake_category = routes.LeaveCategory.query.filter_by(category="test_test_0").first()
        db.delete(fake_category)
        db.commit()


# Methods for adding LeaveRequest to the db for testing purposes
def add_tester_leaverequest():
    q = routes.LeaveRequest(end_date=datetime.date(year=2018, month=4, day=13),
                            start_date=datetime.date(year=2018, month=4, day=10),
                            user_id=(-1), state="approved")
    db.add(q)
    db.commit()
    id_of_request = q.id
    return id_of_request


def remove_tester_leaverequest():
    q = routes.LeaveRequest.query.filter_by(end_date="2018-04-13 00:00:00.000000").first()
    db.delete(q)
    db.commit()


def test_get_leave_request():
    try:
        # Adding test LeaveRequest and setting it's output value to the variable.
        # (it is the ID of the created LeaveRequest)
        id_of_created_leave_request = add_tester_leaverequest()
        # With correct id
        q = routes.get_leave_request(id=id_of_created_leave_request)
        assert isinstance(q, routes.LeaveRequest)
        # Without None id
        q = routes.get_leave_request(id=None)
        assert q is None
        # With string id
        q = routes.get_leave_request(id="asd")
        assert q is None
        # Without existing id
        q = routes.get_leave_request(id=99999998)
        assert q is None
    finally:
        # Removing test LeaveRequest from the db
        remove_tester_leaverequest()


# Methods for adding User to the db for testing purposes
def add_tester_user():
    q = routes.User(email="test_0@invenshure.com", user_group="employee", days=0, notification=0,
                    leave_category_id=(-1))
    db.add(q)
    db.commit()


def remove_tester_user():
    q = routes.User.query.filter_by(email="test_0@invenshure.com").first()
    db.delete(q)
    db.commit()


def test_get_user_by_email():
    try:
        # Adding test user to db
        add_tester_user()
        # With existing email in db
        q = routes.get_user_by_email(email="test_0@invenshure.com")
        assert isinstance(q, routes.User)
        # With None property as email
        q = routes.get_user_by_email(None)
        assert q is None
        # With non existing email (in db)
        q = routes.get_user_by_email(email="test_0@gmail.com")
        assert q is None
        # With integer as email
        q = routes.get_user_by_email(email=12345)
        assert q is None
    finally:
        # Remove test user from db
        remove_tester_user()


def test_get_days_left():
    try:
        # Adding test user and category
        fake_category = routes.LeaveCategory(category="test_test_1", max_days=20)
        db.add(fake_category)
        db.commit()
        fake_user = routes.User(email="test_elek@invenshure.com", user_group="employee", days=0, notification=0,
                                leave_category_id=fake_category.id)
        db.add(fake_user)
        db.commit()
        # With proper user
        q = routes.get_days_left(fake_user)
        assert q == 20

        # With created leave request for 6 days
        data = {"current_user": "test_elek@invenshure.com", "start-date": "03/14/2019", "end-date": "03/19/2019"}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/save_request', data=data)
            assert resp.status_code == 302
        fake_user_2 = routes.User.query.filter_by(email="test_elek@invenshure.com").first()
        q = routes.get_days_left(fake_user_2)
        assert q == 14

        # With created leave request for 16 days ( more than we have ) Does not get created.
        data_2 = {"current_user": "test_elek@invenshure.com", "start-date": "03/20/2019", "end-date": "04/05/2019"}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/save_request', data=data_2)
            assert resp.status_code == 302
        fake_user_3 = routes.User.query.filter_by(email="test_elek@invenshure.com").first()
        # Checks if there is more than 1 leave request
        l_requests = routes.LeaveRequest.query.all()
        assert len(l_requests) == 1
        q = routes.get_days_left(fake_user_3)
        assert q == 14

        # With random email from db
        with pytest.raises(AttributeError):
            routes.get_days_left("test@invenshure.com")
        # With random email not from db
        with pytest.raises(AttributeError):
            routes.get_days_left("test@gmail.com")
        # With random integer
        with pytest.raises(AttributeError):
            routes.get_days_left(1)
        # With None object
        with pytest.raises(AttributeError):
            routes.get_days_left(None)
        # With improper Object
        with pytest.raises(AttributeError):
            routes.get_days_left(fake_category)
    finally:
        # Removing test user and test category
        delete_everything_from_db()


def test_add_to_db():
    try:
        # Adding test user, category, leave request
        fake_category = routes.LeaveCategory(category="test_test_2", max_days=20)
        fake_user = routes.User(email="test_2@invenshure.com", user_group="employee", days=0, notification=0,
                                leave_category_id=fake_category.id)
        fake_leaverequest = routes.LeaveRequest(end_date=datetime.date(year=2018, month=4, day=13),
                                                start_date=datetime.date(year=2018, month=4, day=10),
                                                user_id=(-1), state="approved")
        # # Adding category with null max_days (default 20 so it is added)
        q = routes.LeaveCategory(category="test_test_2", max_days=None)
        routes.add_to_db(q)
        db.delete(q)
        db.commit()
        # Adding with empty string (BUG)
        q = routes.LeaveCategory(category="", max_days=30)
        routes.add_to_db(q)
        db.delete(q)
        # Adding proper objects
        routes.add_to_db(fake_category)
        routes.add_to_db(fake_leaverequest)
        routes.add_to_db(fake_user)
    finally:
        # Removing test user and test category
        delete_everything_from_db()


def test_delete_from_db():
    # Adding test user, category, leave request
    fake_category = routes.LeaveCategory(category="test_test_3", max_days=20)
    fake_user = routes.User(email="test_3@invenshure.com", user_group="employee", days=0, notification=0,
                            leave_category_id=fake_category.id)
    fake_leaverequest = routes.LeaveRequest(end_date=datetime.date(year=2018, month=4, day=13),
                                            start_date=datetime.date(year=2018, month=4, day=10),
                                            user_id=(-1), state="approved")
    db.add(fake_category)
    db.add(fake_leaverequest)
    db.add(fake_user)
    db.commit()
    routes.delete_from_db(fake_category)
    routes.delete_from_db(fake_leaverequest)
    routes.delete_from_db(fake_user)


@mock.patch('flaskr.routes.get_current_user')
def test_get_current_user(get_fake_user, client):
    fake_user = routes.User()
    fake_user.user_group = 'administrator'
    fake_user.email = 'test_admin@invenshure.com'
    fake_user_2 = routes.User()
    fake_user_2.user_group = 'viewer'
    fake_user_2.email = 'test_viewer@invenshure.com'
    fake_user_3 = routes.User()
    fake_user_3.user_group = 'unapproved'
    fake_user_3.email = 'test_unapproved@invenshure.com'
    fake_user_4 = routes.User()
    fake_user_4.user_group = 'employee'
    fake_user_4.email = 'employee@invenshure.com'
    # Admin test
    get_fake_user.return_value = fake_user
    assert (get_fake_user().user_group == 'administrator')
    resp = client.get('/admin')
    assert resp.status_code == 200
    # Viewer test
    get_fake_user.return_value = fake_user_2
    assert (get_fake_user().user_group == 'viewer')
    resp = client.get('/requests')
    assert resp.status_code == 302
    # Unapproved test
    get_fake_user.return_value = fake_user_3
    assert (get_fake_user().user_group == 'unapproved')
    resp = client.get('/save_request')
    assert resp.status_code == 302
    # Employee test
    get_fake_user.return_value = fake_user_4
    assert (get_fake_user().user_group == 'employee')
    resp = client.get('/handle_request')
    assert resp.status_code == 302


def test_create_default_cat():
    # With one category in the db
    try:
        # With empty db
        categories = routes.LeaveCategory.query.all()
        assert len(categories) == 0
        for cat in categories:
            assert cat is None
        routes.create_default_cat()
        categories_2 = routes.LeaveCategory.query.all()
        assert len(categories_2) == 2
        # Checking if the 2 categories were created
        for cat in categories_2:
            assert isinstance(cat, routes.LeaveCategory)
        cat1 = routes.LeaveCategory.query.filter_by(category="Young").first()
        assert cat1.max_days == 20
        cat2 = routes.LeaveCategory.query.filter_by(max_days=30).first()
        assert cat2.category == "Old"
        # remove 1 category
        cat2 = routes.LeaveCategory.query.filter_by(max_days=30).first()
        db.delete(cat2)
        db.commit()
        # Calling the method again, expecting only 1 category
        routes.create_default_cat()
        categories_3 = routes.LeaveCategory.query.all()
        assert len(categories_3) == 1
    finally:
        db.query(routes.LeaveCategory).delete()
        db.commit()


# Checks if we are trying to visit /report endpoint without being logged in
def test_report(client):
    resp = client.get('/report')
    assert b"Redirecting" in resp.data


# Checks if we are trying to visit /report endpoint with being logged in
def test_report_2():
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess["user"] = "test_session_user"
        resp = c.get('/report', follow_redirects=True)
        assert resp.status_code == 200
        assert b"what were you doing when the error occurred" in resp.data


# Checks if we are trying to submit a report without being logged in
def test_report_3(client):
    resp = client.post('/report', follow_redirects=False)
    assert b"/login" in resp.data
    assert b"redirect" in resp.data


# Checks if the report is created after the submit with the given message.
def test_report_4():
    try:
        data = {"report": "Hi! This is the report test body!"}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/report', data=data)
            assert resp.status_code == 200
    finally:
        pass


# Checks if we are redirected after a get request
def test_handle_cat_1(client):
    resp = client.get('/handle_cat', follow_redirects=False)
    assert b"Redirecting..." in resp.data


# Checks if we can delete leave category
def test_handle_cat_2():
    try:
        routes.create_default_cat()
        data = {"current_user": "test@invenshure.com", "delete": 1}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/handle_cat', data=data)
            assert resp.status_code == 302
        q = routes.LeaveCategory.query.all()
        assert len(q) == 1
    finally:
        db.query(routes.LeaveCategory).delete()
        db.commit()


# Checks if we can create new leave category
def test_handle_cat_3():
    try:
        routes.create_default_cat()
        data = {"current_user": "test@invenshure.com", "add": "Test_Category", "max_days": 20}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/handle_cat', data=data)
            assert resp.status_code == 302
        q = routes.LeaveCategory.query.all()
        assert len(q) == 3
    finally:
        db.query(routes.LeaveCategory).delete()
        db.commit()


# Checks if we can create leave category with the same name
def test_handle_cat_4():
    try:
        routes.create_default_cat()
        data = {"current_user": "test@invenshure.com", "add": "Young", "max_days": 20}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/handle_cat', data=data)
            assert resp.status_code == 302
        q = routes.LeaveCategory.query.all()
        assert len(q) == 2
    finally:
        db.query(routes.LeaveCategory).delete()
        db.commit()


# Checks if we are redirected after a get request
def test_handle_acc_1(client):
    resp = client.get('/handle_acc', follow_redirects=False)
    assert b"Redirecting..." in resp.data


# Checks if new user can be accepted
def test_handle_acc_2():
    try:
        user = routes.User(email="test_elek@invenshure.com")
        db.add(user)
        db.commit()
        data = {"approve": "test_elek@invenshure.com"}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/handle_acc', data=data)
            assert resp.status_code == 302
        q = routes.User.query.filter_by(email="test_elek@invenshure.com").first()
        assert q.user_group == "viewer"
    finally:
        delete_everything_from_db()


# Checks if new user can be denied
def test_handle_acc_3():
    try:
        user = routes.User(email="test_elek@invenshure.com")
        db.add(user)
        db.commit()
        data = {"delete": "test_elek@invenshure.com"}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/handle_acc', data=data)
            assert resp.status_code == 302
        q = routes.User.query.filter_by(email="test_elek@invenshure.com").first()
        assert q is None
    finally:
        pass


# Checks if user_group can be modified to employee
def test_handle_acc_4():
    try:
        user = routes.User(email="test_elek@invenshure.com")
        db.add(user)
        db.commit()
        data = {"user": "test_elek@invenshure.com", "group": "employee"}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/handle_acc', data=data)
            assert resp.status_code == 302
        user = routes.User.query.filter_by(email="test_elek@invenshure.com").first()
        assert user.user_group == "employee"
    finally:
        delete_everything_from_db()


# Checks if user_group can be modified to administrator
def test_handle_acc_5():
    try:
        user = routes.User(email="test_elek@invenshure.com")
        db.add(user)
        db.commit()
        data = {"user": "test_elek@invenshure.com", "group": "administrator"}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/handle_acc', data=data)
            assert resp.status_code == 302
        user = routes.User.query.filter_by(email="test_elek@invenshure.com").first()
        assert user.user_group == "administrator"
    finally:
        delete_everything_from_db()


# Checks if user_group can be modified from administrator to unapproved
def test_handle_acc_6():
    try:
        user = routes.User(email="test_elek@invenshure.com")
        db.add(user)
        db.commit()
        data = {"user": "test_elek@invenshure.com", "group": "administrator"}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/handle_acc', data=data)
            assert resp.status_code == 302
        user = routes.User.query.filter_by(email="test_elek@invenshure.com").first()
        assert user.user_group == "administrator"
        db.commit()
        data_2 = {"user": "test_elek@invenshure.com", "group": "unapproved"}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/handle_acc', data=data_2)
            assert resp.status_code == 302
        user = routes.User.query.filter_by(email="test_elek@invenshure.com").first()
        assert user.user_group == "unapproved"
    finally:
        delete_everything_from_db()


# Checks if leave_category is None as default
def test_handle_acc_7():
    try:
        user = routes.User(email="test_elek@invenshure.com")
        db.add(user)
        db.commit()
        data = {"user": "test_elek@invenshure.com", "group": "administrator"}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/handle_acc', data=data)
            assert resp.status_code == 302
        user = routes.User.query.filter_by(email="test_elek@invenshure.com").first()
        assert user.leave_category_id is None
    finally:
        delete_everything_from_db()


# Checks if leave_category can be set
def test_handle_acc_8():
    try:
        routes.create_default_cat()
        user = routes.User(email="test_elek@invenshure.com")
        db.add(user)
        db.commit()
        data = {"user": "test_elek@invenshure.com", "group": "employee"}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/handle_acc', data=data)
            assert resp.status_code == 302
        db.commit()
        data_2 = {"user": "test_elek@invenshure.com", "category": 1}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/handle_acc', data=data_2)
            assert resp.status_code == 302
        user = routes.User.query.filter_by(email="test_elek@invenshure.com").first()
        assert user.leave_category_id == 1
    finally:
        delete_everything_from_db()


# Checks if leave_category is can be changed
def test_handle_acc_9():
    try:
        routes.create_default_cat()
        user = routes.User(email="test_elek@invenshure.com")
        db.add(user)
        db.commit()
        data = {"user": "test_elek@invenshure.com", "group": "employee"}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/handle_acc', data=data)
            assert resp.status_code == 302
        db.commit()
        data_2 = {"user": "test_elek@invenshure.com", "category": 1}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/handle_acc', data=data_2)
            assert resp.status_code == 302
        user = routes.User.query.filter_by(email="test_elek@invenshure.com").first()
        assert user.leave_category_id == 1
        db.commit()
        data_3 = {"user": "test_elek@invenshure.com", "category": 2}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/handle_acc', data=data_3)
            assert resp.status_code == 302
        user = routes.User.query.filter_by(email="test_elek@invenshure.com").first()
        assert user.leave_category_id == 2
    finally:
        delete_everything_from_db()


# Checks if notification is set and can be changed
def test_handle_acc_10():
    try:
        user = routes.User(email="test_elek@invenshure.com")
        db.add(user)
        db.commit()
        data = {"user": "test_elek@invenshure.com", "group": "employee"}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/handle_acc', data=data)
            assert resp.status_code == 302
        user = routes.User.query.filter_by(email="test_elek@invenshure.com").first()
        assert user.notification is True
        data_2 = {"on": "test_elek@invenshure.com"}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/handle_acc', data=data_2)
            assert resp.status_code == 302
        user = routes.User.query.filter_by(email="test_elek@invenshure.com").first()
        assert user.notification is False
        data_3 = {"off": "test_elek@invenshure.com"}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/handle_acc', data=data_3)
            assert resp.status_code == 302
        user = routes.User.query.filter_by(email="test_elek@invenshure.com").first()
        assert user.notification is True
    finally:
        delete_everything_from_db()


# Checks if user's leave_category sets None after assigned category gets deleted
def test_handle_acc_11():
    try:
        routes.create_default_cat()
        user = routes.User(email="test_elek@invenshure.com")
        db.add(user)
        db.commit()
        data = {"user": "test_elek@invenshure.com", "group": "employee"}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/handle_acc', data=data)
            assert resp.status_code == 302
        db.commit()
        data_2 = {"user": "test_elek@invenshure.com", "category": 2}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/handle_acc', data=data_2)
            assert resp.status_code == 302
        user = routes.User.query.filter_by(email="test_elek@invenshure.com").first()
        assert user.leave_category_id == 2
        q = routes.LeaveCategory.query.filter_by(id=2).first()
        db.delete(q)
        db.commit()
        assert user.leave_category_id is None
    finally:
        delete_everything_from_db()


# Checks if we are redirected after a get request
def test_handle_request_1(client):
    resp = client.get('/handle_request', follow_redirects=False)
    assert b"Redirecting..." in resp.data


# Checks if the request changes status from pending to approved
def test_handle_request_2():
    try:
        routes.create_default_cat()
        user = routes.User(email="test_elek@invenshure.com", user_group="employee", leave_category_id=1)
        leave_request = routes.LeaveRequest(end_date=datetime.date(year=2018, month=4, day=13),
                                            start_date=datetime.date(year=2018, month=4, day=10),
                                            user_id=1, state="pending")
        db.add(user)
        db.add(leave_request)
        db.commit()
        data = {"site": "requests", "accept": 1}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/handle_request', data=data)
            assert resp.status_code == 302
        l_request = routes.LeaveRequest.query.filter_by(user_id=1).first()
        assert l_request.state == "accepted"
    finally:
        delete_everything_from_db()


# Checks if the request changes status from pending to declined
def test_handle_request_3():
    try:
        routes.create_default_cat()
        user = routes.User(email="test_elek@invenshure.com", user_group="employee", leave_category_id=1)
        leave_request = routes.LeaveRequest(end_date=datetime.date(year=2018, month=4, day=13),
                                            start_date=datetime.date(year=2018, month=4, day=10),
                                            user_id=1, state="pending")
        db.add(user)
        db.add(leave_request)
        db.commit()
        data = {"site": "requests", "decline": 1}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/handle_request', data=data)
            assert resp.status_code == 302
        l_request = routes.LeaveRequest.query.filter_by(user_id=1).first()
        assert l_request.state == "declined"
    finally:
        delete_everything_from_db()


# Checks if the request changes status from pending to declined and than to approved
def test_handle_request_4():
    try:
        routes.create_default_cat()
        user = routes.User(email="test_elek@invenshure.com", user_group="employee", leave_category_id=1)
        leave_request = routes.LeaveRequest(end_date=datetime.date(year=2018, month=4, day=13),
                                            start_date=datetime.date(year=2018, month=4, day=10),
                                            user_id=1, state="pending")
        db.add(user)
        db.add(leave_request)
        db.commit()
        data = {"site": "requests", "decline": 1}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/handle_request', data=data)
            assert resp.status_code == 302
        l_request = routes.LeaveRequest.query.filter_by(user_id=1).first()
        assert l_request.state == "declined"
        db.commit()
        data = {"site": "requests", "accept": 1}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/handle_request', data=data)
            assert resp.status_code == 302
        l_request = routes.LeaveRequest.query.filter_by(user_id=1).first()
        assert l_request.state == "accepted"
    finally:
        delete_everything_from_db()


# Creating a request with an employee for 6 days
def test_save_request_1():
    try:
        # Adding test user and category
        routes.create_default_cat()
        fake_user = routes.User(email="test_elek@invenshure.com", user_group="employee", days=0, notification=0,
                                leave_category_id=1)
        db.add(fake_user)
        db.commit()

        # With created leave request for 6 days
        data = {"current_user": "test_elek@invenshure.com", "start-date": "03/14/2019", "end-date": "03/19/2019"}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/save_request', data=data)
            assert resp.status_code == 302
        l_req = routes.LeaveRequest.query.filter_by(end_date="2019-03-19 00:00:00.000000").first()
        assert l_req.state == "pending"
    finally:
        delete_everything_from_db()


# Creating a request with an administrator for 6 days and checks if the status is accepted automatically
def test_save_request_2():
    try:
        # Adding test user and category
        routes.create_default_cat()
        fake_user = routes.User(email="test_elek@invenshure.com", user_group="administrator", days=0, notification=0,
                                leave_category_id=1)
        db.add(fake_user)
        db.commit()

        # With created leave request for 6 days
        data = {"current_user": "test_elek@invenshure.com", "start-date": "03/14/2019", "end-date": "03/19/2019"}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/save_request', data=data)
            assert resp.status_code == 302
        l_req = routes.LeaveRequest.query.filter_by(end_date="2019-03-19 00:00:00.000000").first()
        assert l_req.state == "accepted"
    finally:
        delete_everything_from_db()


# Trying to create a request with administrator for more days than we have
def test_save_request_3():
    try:
        # Adding test user and category
        routes.create_default_cat()
        fake_user = routes.User(email="test_elek@invenshure.com", user_group="administrator", days=0, notification=0,
                                leave_category_id=1)
        db.add(fake_user)
        db.commit()

        # With created leave request for 6 days
        data = {"current_user": "test_elek@invenshure.com", "start-date": "03/14/2019", "end-date": "03/19/2019"}
        data_2 = {"current_user": "test_elek@invenshure.com", "start-date": "04/01/2019", "end-date": "04/25/2019"}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/save_request', data=data)
            assert resp.status_code == 302
            resp = client.post('/save_request', data=data_2)
            assert resp.status_code == 302
        l_requests = routes.LeaveRequest.query.all()
        assert len(l_requests) == 1
        user = routes.User.query.filter_by(email="test_elek@invenshure.com").first()
        assert user.days == 6
    finally:
        delete_everything_from_db()


# Trying to create a request with employee for more days than we have
def test_save_request_4():
    try:
        # Adding test user and category
        routes.create_default_cat()
        fake_user = routes.User(email="test_elek@invenshure.com", user_group="employee", days=0, notification=0,
                                leave_category_id=1)
        db.add(fake_user)
        db.commit()

        # With created leave request for 6 days
        data = {"current_user": "test_elek@invenshure.com", "start-date": "03/14/2019", "end-date": "03/19/2019"}
        data_2 = {"current_user": "test_elek@invenshure.com", "start-date": "04/01/2019", "end-date": "04/25/2019"}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/save_request', data=data)
            assert resp.status_code == 302
            resp = client.post('/save_request', data=data_2)
            assert resp.status_code == 302
        l_requests = routes.LeaveRequest.query.all()
        assert len(l_requests) == 1
        user = routes.User.query.filter_by(email="test_elek@invenshure.com").first()
        assert user.days == 6
    finally:
        delete_everything_from_db()


# Trying to create request with bigger start date than end date // Fails until i don't fix this bug
def test_save_request_5():
    try:
        # Adding test user and category
        routes.create_default_cat()
        fake_user = routes.User(email="test_elek@invenshure.com", user_group="administrator", days=0, notification=0,
                                leave_category_id=1)
        db.add(fake_user)
        db.commit()

        # With created leave request for -1 days
        data = {"current_user": "test_elek@invenshure.com", "start-date": "03/14/2019", "end-date": "03/13/2019"}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/save_request', data=data)
            assert resp.status_code == 302
        l_requests = routes.LeaveRequest.query.all()
        assert len(l_requests) == 1
    finally:
        delete_everything_from_db()


# Trying to create requests with invalid inputs
def test_save_request_6():
    try:
        # Adding test user and category
        routes.create_default_cat()
        fake_user = routes.User(email="test_elek@invenshure.com", user_group="administrator", days=0, notification=0,
                                leave_category_id=1)
        db.add(fake_user)
        db.commit()

        data = {"current_user": "test_elek@invenshure.com", "start-date": "03/14/2019", "end-date": "xx/x/"}
        data_2 = {"current_user": "test_elek@invenshure.com", "start-date": "xx/xx/20xx19", "end-date": "xx/x/"}
        data_3 = {"current_user": "test_elek@invenshure.com", "start-date": "//", "end-date": "//"}
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user'] = 'test_elek@invenshure.com'
            resp = client.post('/save_request', data=data)
            assert resp.status_code == 302
            resp = client.post('/save_request', data=data_2)
            assert resp.status_code == 302
            resp = client.post('/save_request', data=data_3)
            assert resp.status_code == 302
        l_requests = routes.LeaveRequest.query.all()
        assert len(l_requests) == 0
    finally:
        delete_everything_from_db()


# Sending post request to account endpoint
def test_account_1(client):
    rv = client.post('/account')
    assert b"Method Not Allowed" in rv.data


# Sending get request, expecting proper values
def test_account_2(mocker):
    class MockedUserInfo:
        def __init__(self, userinfo):
            self.data = userinfo

    try:
        routes.create_default_cat()
        fake_user = routes.User(email="test_elek@invenshure.com", user_group="administrator", days=0,
                                notification=0,
                                leave_category_id=1)
        db.add(fake_user)
        db.commit()

        json_data = {
            "id": "101843067871304637814",
            "email": "test_elek@invenshure.com",
            "verified_email": "True",
            "picture": "aaaaaaaaaa.jpeg",
            "hd": "invenshure.com"
        }

        with app.test_client() as client:
            mocker.patch('flaskr.routes.google.get', return_value=MockedUserInfo(json_data))
            resp = client.get('/account')
            assert resp.status_code == 200
            assert b"Group" in resp.data
            assert b"administrator" in resp.data
            assert b"20" in resp.data
    finally:
        delete_everything_from_db()


# Sending get request with None leavecategory
def test_account_3(mocker):
    class MockedUserInfo:
        def __init__(self, userinfo):
            self.data = userinfo

    try:
        routes.create_default_cat()
        fake_user = routes.User(email="test_elek@invenshure.com", user_group="administrator", days=0,
                                notification=0,
                                leave_category_id=None)
        db.add(fake_user)
        db.commit()

        json_data = {
            "id": "101843067871304637814",
            "email": "test_elek@invenshure.com",
            "verified_email": "True",
            "picture": "aaaaaaaaaa.jpeg",
            "hd": "invenshure.com"
        }

        with app.test_client() as client:
            mocker.patch('flaskr.routes.google.get', return_value=MockedUserInfo(json_data))
            resp = client.get('/account')
            assert resp.status_code == 200
            assert b"Group" in resp.data
            assert b"administrator" in resp.data
            assert b"You don&#39;t have a leave category yet." in resp.data
    finally:
        delete_everything_from_db()


# Checks response from /requests endpoint With 1 request
def test_requests_1(mocker):
    class MockedUserInfo:
        def __init__(self, userinfo):
            self.data = userinfo

    try:
        routes.create_default_cat()
        fake_user = routes.User(email="test_elek@invenshure.com", user_group="administrator", days=0,
                                notification=0,
                                leave_category_id=1)
        leave_request = routes.LeaveRequest(end_date=datetime.date(year=2018, month=4, day=11),
                                            start_date=datetime.date(year=2018, month=4, day=10),
                                            user_id=1, state="pending")

        db.add(fake_user)
        db.add(leave_request)
        db.commit()

        json_data = {
            "id": "101843067871304637814",
            "email": "test_elek@invenshure.com",
            "verified_email": "True",
            "picture": "aaaaaaaaaa.jpeg",
            "hd": "invenshure.com"
        }

        with app.test_client() as client:
            mocker.patch('flaskr.routes.google.get', return_value=MockedUserInfo(json_data))
            resp = client.get('/requests')
            assert resp.status_code == 200
            assert b"pending" in resp.data
            assert b"test_elek@invenshure.com" in resp.data
            assert b"Browse Leave Requests" in resp.data
            assert b"2018-04-10"
    finally:
        delete_everything_from_db()


# Checks response from /requests endpoint With 11 request
def test_requests_2(mocker):
    class MockedUserInfo:
        def __init__(self, userinfo):
            self.data = userinfo

    try:
        routes.create_default_cat()
        fake_user = routes.User(email="test_elek@invenshure.com", user_group="administrator", days=0,
                                notification=0,
                                leave_category_id=1)
        db.add(fake_user)
        db.commit()
        x = 0
        while x < 11:
            leave_request = routes.LeaveRequest(end_date=datetime.date(year=2018, month=4, day=11),
                                                start_date=datetime.date(year=2018, month=4, day=10),
                                                user_id=1, state="pending")

            db.add(leave_request)
            db.commit()
            x = x + 1

        json_data = {
            "id": "101843067871304637814",
            "email": "test_elek@invenshure.com",
            "verified_email": "True",
            "picture": "aaaaaaaaaa.jpeg",
            "hd": "invenshure.com"
        }

        with app.test_client() as client:
            mocker.patch('flaskr.routes.google.get', return_value=MockedUserInfo(json_data))
            resp = client.get('/requests')
            assert resp.status_code == 200
            assert b"pending" in resp.data
            assert b"test_elek@invenshure.com" in resp.data
            assert b"Browse Leave Requests" in resp.data
            assert b"2018-04-10" in resp.data
            assert b"Next" in resp.data
    finally:
        delete_everything_from_db()


# Checks if /admin endpoint gives back the expected values for administrator user
def test_admin_1(mocker):
    class MockedUserInfo:
        def __init__(self, userinfo):
            self.data = userinfo

    try:
        routes.create_default_cat()
        fake_user = routes.User(email="test_elni_jo@invenshure.com", user_group="administrator", days=0,
                                notification=0,
                                leave_category_id=1)
        fake_user_2 = routes.User(email="test_elek@invenshure.com", user_group="unapproved", days=0,
                                  notification=0,
                                  leave_category_id=None)
        leave_request = routes.LeaveRequest(end_date=datetime.date(year=2018, month=4, day=11),
                                            start_date=datetime.date(year=2018, month=4, day=10),
                                            user_id=1, state="pending")

        db.add(fake_user)
        db.add(fake_user_2)
        db.add(leave_request)
        db.commit()

        json_data = {
            "id": "101843067871304637814",
            "email": "test_elni_jo@invenshure.com",
            "verified_email": "True",
            "picture": "aaaaaaaaaa.jpeg",
            "hd": "invenshure.com"
        }

        with app.test_client() as client:
            mocker.patch('flaskr.routes.google.get', return_value=MockedUserInfo(json_data))
            resp = client.get('/admin')
            assert resp.status_code == 200
            assert b"Approve" in resp.data
            assert b"Decline" in resp.data
            assert b"test_elek@invenshure.com" in resp.data
            assert b"test_elni_jo@invenshure.com" in resp.data
            assert b"Pending Accounts" in resp.data
            assert b"2018-04-11"
            assert b"Leave Category"
            assert b"User Group"
            assert b"New category"
            assert b"Add"
    finally:
        delete_everything_from_db()


# Checks if /admin endpoint redirects for a non administrator user
def test_admin_2(mocker):
    class MockedUserInfo:
        def __init__(self, userinfo):
            self.data = userinfo

    try:
        routes.create_default_cat()
        fake_user = routes.User(email="test_elni_jo@invenshure.com", user_group="employee", days=0,
                                notification=0,
                                leave_category_id=1)
        fake_user_2 = routes.User(email="test_elek@invenshure.com", user_group="unapproved", days=0,
                                  notification=0,
                                  leave_category_id=None)
        leave_request = routes.LeaveRequest(end_date=datetime.date(year=2018, month=4, day=11),
                                            start_date=datetime.date(year=2018, month=4, day=10),
                                            user_id=1, state="pending")

        db.add(fake_user)
        db.add(fake_user_2)
        db.add(leave_request)
        db.commit()

        json_data = {
            "id": "101843067871304637814",
            "email": "test_elni_jo@invenshure.com",
            "verified_email": "True",
            "picture": "aaaaaaaaaa.jpeg",
            "hd": "invenshure.com"
        }

        with app.test_client() as client:
            mocker.patch('flaskr.routes.google.get', return_value=MockedUserInfo(json_data))
            resp = client.get('/admin', follow_redirects=False)
            assert resp.status_code == 302
            assert b"Redirecting..." in resp.data
            assert b"Leave Category" not in resp.data
            assert b"User Group" not in resp.data
            assert b"New category" not in resp.data
    finally:
        delete_everything_from_db()


