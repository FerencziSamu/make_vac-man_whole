from unittest.mock import Mock
from flask_mail import Message
from flaskr import routes, logging
import pytest, unittest, datetime, requests

# Global variable for db calling
db = routes.db.session


def login(client, username, password):
    return client.post('/login/authorized', data=dict(
        username=username,
        password=password
    ), follow_redirects=True)


def logout(client):
    return client.get('/logout', follow_redirects=True)


def test_login_logout(client):
    rv = login(client, "Username", "Password")
    assert b'The method is not allowed for the requested URL.' in rv.data

    rv = logout(client)
    assert rv.status_code == 200


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
    # With correct mapping
    q = routes.get_leaveCategory(field={'id': 1})
    assert isinstance(q, routes.LeaveCategory)
    # Without mapping
    with pytest.raises(TypeError):
        routes.get_leaveCategory(field=None)
    # With empty mapping
    q = routes.get_leaveCategory(field={'': ''})
    assert q is None
    # 'LeaveCategory' has no attribute 'asd'
    q = routes.get_leaveCategory(field={'asd': 1})
    assert q is None
    # 'LeaveCategory' has no property 'asd'
    q = routes.get_leaveCategory(field={'id': 'asd'})
    assert q is None

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


def test_getLeaveRequest():
    try:
        # Adding test LeaveRequest and setting it's output value to the variable.
        # (it is the ID of the created LeaveRequest)
        id_of_created_leave_request = add_tester_leaverequest()
        # With correct id
        q = routes.getLeaveRequest(id=id_of_created_leave_request)
        assert isinstance(q, routes.LeaveRequest)
        # Without None id
        q = routes.getLeaveRequest(id=None)
        assert q is None
        # With string id
        q = routes.getLeaveRequest(id="asd")
        assert q is None
        # Without existing id
        q = routes.getLeaveRequest(id=99999998)
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


def test_getUserByEmail():
    try:
        # Adding test user to db
        add_tester_user()
        # With existing email in db
        q = routes.getUserByEmail(email="test_0@invenshure.com")
        assert isinstance(q, routes.User)
        # With None property as email
        q = routes.getUserByEmail(None)
        assert q is None
        # With non existing email (in db)
        q = routes.getUserByEmail(email="test_0@gmail.com")
        assert q is None
        # With integer as email
        q = routes.getUserByEmail(email=12345)
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
        p = routes.get_days_left(fake_user)
        assert p == 20
        # With created leave request for 6 days
        url = "http://127.0.0.1:5000/save_request"
        data = {"current_user": "test@invenshure.com", "start-date": "03/14/2019", "end-date": "03/19/2019"}
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
        pass
        # Removing test user and test category
        fake_user = routes.User.query.filter_by(email="test@invenshure.com").first()
        fake_category = routes.LeaveCategory.query.filter_by(category="test_test_1").first()
        fake_request = routes.LeaveRequest.query.filter_by(user_id=fake_user.id).first()
        logging.info(str(fake_user.days) + "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
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
        fake_leaverequest = routes.LeaveRequest(end_date=datetime.date(year=2018, month=4, day=10),
                                start_date=datetime.date(year=2018, month=4, day=13),
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
        fake_leaverequest = routes.LeaveRequest.query.filter_by(end_date="2018-04-10 00:00:00.000000").first()
        db.delete(fake_leaverequest)
        db.delete(fake_category)
        db.delete(fake_user)
        db.commit()

def test_delete_from_db():
    # Adding test user, category, leave request
    fake_category = routes.LeaveCategory(category="test_test_3", max_days=20)
    fake_user = routes.User(email="test_3@invenshure.com", user_group="employee", days=0, notification=0,
                            leave_category_id=fake_category.id)
    fake_leaverequest = routes.LeaveRequest(end_date=datetime.date(year=2018, month=4, day=10),
                            start_date=datetime.date(year=2018, month=4, day=13),
                            user_id=(-1), state="approved")
    routes.add_to_db(fake_category)
    routes.add_to_db(fake_leaverequest)
    routes.add_to_db(fake_user)
    routes.delete_from_db(fake_category)
    routes.delete_from_db(fake_leaverequest)
    routes.delete_from_db(fake_user)
