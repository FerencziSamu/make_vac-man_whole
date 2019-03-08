from unittest import mock
from unittest.mock import Mock
from flask_mail import Message
from flaskr import routes, logging
import pytest, unittest, datetime, requests
from flaskr import app


# Deleting all data from db before testing
routes.db.session.query(routes.User).delete()
routes.db.session.query(routes.LeaveRequest).delete()
routes.db.session.query(routes.LeaveCategory).delete()
routes.db.session.commit()

# Global variable for db calling

db = routes.db.session


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
    msg.body = "test_email_Asd_asd"
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
    q = routes.User(email="test_0@invenshure.com", user_group="employee", days=0, notification=0, leave_category_id=(-1))
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
        fake_user = routes.User(email="test@invenshure.com", user_group="employee", days=0, notification=0,
                                leave_category_id=fake_category.id)
        db.add(fake_user)
        db.commit()
        # With proper user
        q = routes.get_days_left(fake_user)
        assert q == 20
        # With created leave request for 6 days
        url = "http://127.0.0.1:5000/save_request"
        data = {"current_user": "test@invenshure.com", "start-date": "03/14/2019", "end-date": "03/19/2019"}
        requests.post(url, data)
        db.commit()
        q = routes.get_days_left(fake_user)
        assert q == 14
        # With created leave request for 16 days ( more than we have ) Does not get created.
        url = "http://127.0.0.1:5000/save_request"
        data = {"current_user": "test@invenshure.com", "start-date": "03/20/2019", "end-date": "04/05/2019"}
        requests.post(url, data)
        db.commit()
        q = routes.get_days_left(fake_user)
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
        fake_user = routes.User.query.filter_by(email="test@invenshure.com").first()
        fake_category = routes.LeaveCategory.query.filter_by(category="test_test_1").first()
        fake_request = routes.LeaveRequest.query.filter_by(user_id=fake_user.id).first()
        db.delete(fake_request)
        db.delete(fake_user)
        db.delete(fake_category)
        db.commit()


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
        fake_user = routes.User.query.filter_by(email="test_2@invenshure.com").first()
        fake_category = routes.LeaveCategory.query.filter_by(category="test_test_2").first()
        fake_leaverequest = routes.LeaveRequest.query.filter_by(end_date="2018-04-13 00:00:00.000000").first()
        db.delete(fake_leaverequest)
        db.delete(fake_category)
        db.delete(fake_user)
        db.commit()


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
    assert(get_fake_user().user_group == 'administrator')
    resp = client.get('/admin')
    assert resp.status_code == 200
    # Viewer test
    get_fake_user.return_value = fake_user_2
    assert(get_fake_user().user_group == 'viewer')
    resp = client.get('/requests')
    assert resp.status_code == 302
    # Unapproved test
    get_fake_user.return_value = fake_user_3
    assert(get_fake_user().user_group == 'unapproved')
    resp = client.get('/save_request')
    assert resp.status_code == 302
    # Employee test
    get_fake_user.return_value = fake_user_4
    assert(get_fake_user().user_group == 'employee')
    resp = client.get('/handle_request')
    assert resp.status_code == 302

# Will return to it
# @mock.patch('flaskr.routes.authorized')
# def test_authorized(get_fake_google_response, client):
#     fake_google_response = {
#     # 'access_token': '',
#     # 'expires_in': 3600,
#     # 'scope': 'https://www.googleapis.com/auth/userinfo.email openid',
#     # 'token_type': 'Bearer',
#     # 'id_token': ''
#     }
#     get_fake_google_response.return_value = fake_google_response
#     resp = client.get('/login')
#     assert resp.status_code == 302


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
