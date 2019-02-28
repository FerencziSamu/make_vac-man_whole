from unittest.mock import Mock
from flask_mail import Message
from flaskr import routes, logging, models
import pytest, unittest, datetime


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
    assert q is not None
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
    q = routes.LeaveRequest(end_date=datetime.date(year=2018, month=4, day=10),
                            start_date=datetime.date(year=2018, month=4, day=13),
                            user_id=(-1), state="approved")
    routes.db.session.add(q)
    routes.db.session.commit()
    idk = q.id
    return idk

def remove_tester_leaverequest():
    q = routes.LeaveRequest.query.filter_by(end_date="2018-04-10 00:00:00.000000").first()
    routes.db.session.delete(q)
    routes.db.session.commit()


def test_getLeaveRequest():
    # Adding test LeaveRequest and setting it's output value to the variable. (it is the ID of the created LeaveRequest)
    id_of_created_leave_request = add_tester_leaverequest()
    # With correct id
    q = routes.getLeaveRequest(id=id_of_created_leave_request)
    assert q is not None
    # Without None id
    q = routes.getLeaveRequest(id=None)
    assert q is None
    # With string id
    q = routes.getLeaveRequest(id="asd")
    assert q is None
    # Without existing id
    q = routes.getLeaveRequest(id=99999998)
    assert q is None
    # Removing test LeaveRequest from the db
    remove_tester_leaverequest()
