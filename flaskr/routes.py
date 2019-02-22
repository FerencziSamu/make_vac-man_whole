from smtplib import SMTPException
from flask import redirect, url_for, session, request, render_template, flash
from flaskr import app, db, mail, logging
from flaskr.models import User, LeaveRequest, LeaveCategory
from .decorators import asynchronous
from flask_oauthlib.client import OAuth, OAuthException
from flask_mail import Message
from sqlalchemy import exc
import datetime
import time
import json

REDIRECT_URI = '/oauth2callback'  # one of the Redirect URIs from Google APIs console

oauth = OAuth()

google = oauth.remote_app('google',
                          base_url='https://www.googleapis.com/oauth2/v1/',
                          authorize_url='https://accounts.google.com/o/oauth2/auth',
                          request_token_url=None,
                          request_token_params={'scope': 'email'},
                          access_token_url='https://accounts.google.com/o/oauth2/token',
                          access_token_method='POST',
                          consumer_key=app.config.get('GOOGLE_ID'),
                          consumer_secret=app.config.get('GOOGLE_SECRET'))


@app.route('/')
def index():
    if 'user' in session:
        current_user = get_current_user()
        return render_template('index.html', current_user=current_user)
    return render_template('index.html', current_user=None)

@app.route('/admin')
def admin():
    try:
        current_user = get_current_user()
        if current_user.user_group == 'administrator':
            users = User.query.all()
            leave_categories = LeaveCategory.query.all()
            page = request.args.get('page', 1, type=int)
            leave_requests = LeaveRequest.query.filter_by(state='pending').paginate(page, app.config.get(
                'REQUESTS_PER_PAGE_ADMIN'), False)
            next_url = url_for('admin', page=leave_requests.next_num) \
                if leave_requests.has_next else None
            prev_url = url_for('admin', page=leave_requests.prev_num) \
                if leave_requests.has_prev else None
            return render_template('admin.html', users=users, leave_requests=leave_requests.items, next_url=next_url,
                                   prev_url=prev_url, leave_categories=leave_categories,
                                   user_groups=app.config.get('USER_GROUPS'), current_user=current_user)
        return redirect(url_for('index'))
    except OAuthException as e:
        logging.exception("Exception: " + str(e))
        return redirect(url_for('logout'))
    except AttributeError as e:
        logging.error("Error " + str(e))
        return redirect(url_for('index'))

@app.route('/requests')
def requests():
    try:
        current_user = get_current_user()
        if current_user.user_group == 'administrator':
            page = request.args.get('page', 1, type=int)
            leave_requests = LeaveRequest.query.order_by(LeaveRequest.start_date.asc()).paginate(page, app.config.get(
                'REQUESTS_PER_PAGE'), False)
            next_url = url_for('requests', page=leave_requests.next_num) \
                if leave_requests.has_next else None
            prev_url = url_for('requests', page=leave_requests.prev_num) \
                if leave_requests.has_prev else None
            return render_template('requests.html', leave_requests=leave_requests.items, next_url=next_url,
                                   prev_url=prev_url, current_user=current_user)
        return redirect(url_for('index'))
    except AttributeError as e:
        logging.error("Error " + str(e))
    return redirect(url_for('index'))

@app.route('/account')
def account():
    try:
        current_user = get_current_user()
        if current_user.leave_category is None:
            days_left = "You don't have a leave category yet."
        else:
            days_left = get_days_left(current_user)
        return render_template('account.html', current_user=current_user, days_left=days_left)
    except AttributeError as e:
        logging.error("Error: " + str(e))
        return redirect(url_for('logout'))

@app.route('/save_request', methods=["GET", "POST"])
def save_request():
    try:
        email = request.form.get('current_user')
        current_user = getUserByEmail(email=email)
        if current_user.user_group == 'viewer' or current_user.user_group == 'unapproved':
            return redirect(url_for('index'))
        start_date_split = request.form.get('start-date').split("/")
        end_date_split = request.form.get('end-date').split("/")
        start_date = create_start_date(start_date_split)
        end_date = create_end_date(end_date_split)
        days = (end_date - start_date).days
        if days + 1 <= get_days_left(current_user):
            leave_request = LeaveRequest(start_date=start_date,
                                         end_date=end_date,
                                         state='pending',
                                         user_id=current_user.id)
            if current_user.user_group == 'administrator':
                leave_request.state = 'accepted'
            current_user.days += days + 1
            add_to_db(leave_request)
            change = current_user.email + " created a leave request."
            send_email(change)
            logging.info(session['user'] + " created a leave request with id:" + str(leave_request.id))
            return redirect(url_for('index'))
        flash("You only have " + str(get_days_left(current_user)) + " days left!")
        return redirect(url_for('index'))
    except AttributeError as e:
        logging.error("Error " + str(e))
        return redirect(url_for('index'))

@app.route('/handle_request', methods=["POST", "GET"])
def handle_request():
    if request.method == 'POST':
        accept_request = request.form.get('accept')
        decline_request = request.form.get('decline')
        if accept_request is not None:
            leave_request = getLeaveRequest(id=accept_request)
            if leave_request.state != 'pending':
                days = leave_request.end_date - leave_request.start_date
                leave_request.user.days += days.days + 1
            leave_request.state = 'accepted'
            db.session.commit()
            change = leave_request.user.email + "'s leave request has been accepted."
            send_email(change, leave_request.user.email)
            logging.info("Leave request by " + leave_request.user.email + " id: " + accept_request + ", has been "
            "accepted by " + session['user'])
        else:
            leave_request = getLeaveRequest(id=decline_request)
            leave_request.state = 'declined'
            days_back = leave_request.end_date - leave_request.start_date
            leave_request.user.days -= days_back.days + 1
            db.session.commit()
            change = leave_request.user.email + "'s leave request has been declined."
            send_email(change, leave_request.user.email)
            logging.info("Leave request by " + leave_request.user.email + " id: " + decline_request + ", has been "
            "declined by " + session['user'])
        if request.form.get('site'):
            return redirect(url_for('requests'))
    return redirect(url_for('index'))

@app.route('/handle_acc', methods=["GET", "POST"])
def handle_acc():
    if request.method == 'POST':
        delete_email = request.form.get('delete')
        approve_email = request.form.get('approve')
        group = request.form.get('group')
        category = request.form.get('category')
        user_email = request.form.get('user')
        on = request.form.get('on')
        off = request.form.get('off')
        if on or off is not None:
            if on is not None:
                user = getUserByEmail(email=on)
                user.notification = False
                db.session.commit()
                logging.info("Notification has been set to FALSE by " + session['user'])
            else:
                user = getUserByEmail(email=off)
                user.notification = True
                db.session.commit()
                logging.info("Notification has been set to TRUE by " + session['user'])
            return redirect(url_for('account'))

        if delete_email is not None:
            user = getUserByEmail(email=delete_email)
            change = "The registration of " + user.email + " has been declined!"
            delete_from_db(user)
            send_email(change, user_email)
            logging.info(user.email + " has been declined by " + session['user'])
        elif approve_email is not None:
            user = getUserByEmail(email=approve_email)
            user.user_group = 'viewer'
            db.session.commit()
            change = user.email + " has been approved."
            send_email(change, user.email)
            logging.info(user.email + " has been accepted by " + session['user'])
        elif category is not None:
            user = getUserByEmail(email=user_email)
            user.leave_category_id = category
            db.session.commit()
            change = user.email + "'s category has been changed."
            send_email(change, user.email)
            cat = LeaveCategory.query.filter_by(id=category).first()
            logging.info(user.email + " 's category has been changed to " + cat.category + " by " + session['user'])
        else:
            user = getUserByEmail(email=user_email)
            user.user_group = group
            db.session.commit()
            change = user.email + "'s user group has been changed."
            send_email(change, user.email)
            logging.info(user.email + " 's user group has been changed to " + user.user_group + " by " + session['user'])
    return redirect(url_for('admin'))

@app.route('/handle_cat', methods=["POST", "GET"])
def handle_cat():
    if request.method == "POST":
        delete = request.form.get('delete')
        new = request.form.get('add')
        max_days = request.form.get('max_days')
        if delete is not None:
            category = get_leaveCategory({'id': delete})
            delete_from_db(category)
            change = category.category + " leave category has been deleted."
            send_email(change)
            logging.info(category.category + " category has been deleted by " + session['user'])
        else:
            cat = LeaveCategory(category=new, max_days=max_days)
            categories = get_leaveCategory({'category': new})
            if categories is None:
                add_to_db(cat)
                change = cat.category + " leave category has been added."
                send_email(change)
                logging.info(cat.category + " category has been created by " + session['user'])
        return redirect(url_for('admin'))
    return redirect(url_for('index'))

@app.route('/report', methods=['GET', 'POST'])
def report():
    try:
        if 'user' in session:
            if request.method == 'GET':
                return render_template('report.html')
            else:
                report_value = request.form['report']
                ts = time.time()
                report_time = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                user = session.get('user')
                f = open("flaskr/reports/" + report_time, "a+")
                f.write(user + " " + report_time + " " + report_value + "\n")
                f.close()
                email = [app.config.get('USER_EMAIL')]
                msg = Message('Vacation Management Error Report',
                              sender='noreply@demo.com',
                              recipients=email)
                msg.body = f'''New report: {user} {report_time} {report_value}'''
                send_async_email(app, msg)
                return render_template('report.html', success=True)
        return redirect(url_for('login'))
    except OAuthException as e:
        logging.exception("Exception " + str(e))
    except Exception as e:
        logging.exception("Exception " + str(e))

@app.route('/login')
def login():
    return google.authorize(callback=url_for('authorized', _external=True))

@app.route('/logout')
def logout():
    session.pop('google_token', None)
    session.pop('user', None)
    return redirect(url_for('index'))

def create_default_cat():
    try:
        categories = LeaveCategory.query.all()
        if not categories:
            young = LeaveCategory(category='Young', max_days='20')
            old = LeaveCategory(category='Old', max_days='30')
            add_to_db(young)
            add_to_db(old)
            logging.info("Default categories have been created.")
    except Exception as e:
        logging.exception("Exception at create_default_cat: " + str(e))

@app.route('/login/authorized')
def authorized():
    try:
        resp = google.authorized_response()
        if resp is None:
            return 'Access denied: reason=%s error=%s' % (
                request.args['error_reason'],
                request.args['error_description']
            )
        session['google_token'] = (resp['access_token'], '')
        raw_data = json.dumps(google.get('userinfo').data)
        data = json.loads(raw_data)
        email = data['email']
        existing = getUserByEmail(email=email)
        session['user'] = email
        logging.info(session['user'] + " has logged in.")
        if existing is None:
            first_user = User.query.all()
            if not first_user:
                user = User(email=email)
                user.user_group = "administrator"
                add_to_db(user)
                create_default_cat()
                change = user.email + " logged in for the first time.You are administrator now!"
                send_email(change)
                session['user'] = user.email
                logging.info(session['user'] + " has logged in.")
                return redirect(url_for('index'))
            user = User(email=email)
            add_to_db(user)
            change = user.email + " logged in for the first time."
            send_email(change)
            session['user'] = user.email
            logging.info(session['user'] + " has logged in.")
        return redirect(url_for('index'))
    except Exception as e:
        logging.exception("Exception at login/authorized: " + str(e))

@google.tokengetter
def get_google_oauth_token():
    return session.get('google_token')

@app.template_filter('dateformat')
def dateformat(date):
    return date.strftime('%Y-%m-%d')

def add_to_db(item):
    try:
        db.session.add(item)
        db.session.commit()
    except exc.SQLAlchemyError as e:
        logging.exception("Exception: " + str(e))

def delete_from_db(item):
    try:
        db.session.delete(item)
        db.session.commit()
    except exc.SQLAlchemyError as e:
        logging.exception("Exception: " + str(e))

def get_current_user():
    try:
        raw_data = json.dumps(google.get('userinfo').data)
        data = json.loads(raw_data)
        email = data['email']
        return getUserByEmail(email=email)
    except KeyError as e:
        logging.error("Error: " + str(e))
        return redirect(url_for('logout'))
    except Exception as e:
        logging.exception("Exception: " + str(e))
        return redirect(url_for('index'))

def get_days_left(user):
    return user.leave_category.max_days - user.days

def getUserByEmail(email):
    try:
        return User.query.filter_by(email=email).first()
    except exc.SQLAlchemyError as e:
        logging.exception("Exception: " + str(e))

def getLeaveRequest(id):
    try:
        return LeaveRequest.query.filter_by(id=id).first()
    except exc.SQLAlchemyError as e:
        logging.exception("Exception: " + str(e))

def get_leaveCategory(field=None):
    try:
        return LeaveCategory.query.filter_by(**field).first()
    except exc.SQLAlchemyError as e:
        logging.exception("Exception: " + str(e))

def create_start_date(start_date_split):
    return datetime.datetime.strptime(start_date_split[2] + '-' + start_date_split[0] + '-' + start_date_split[1],
                                      '%Y-%m-%d')

def create_end_date(end_date_split):
    return datetime.datetime.strptime(end_date_split[2] + '-' + end_date_split[0] + '-' + end_date_split[1], '%Y-%m-%d')

@asynchronous
def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except SMTPException as e:
            logging.exception("Exception: " + str(e))
            pass
        except AssertionError as e:
            logging.error("Error: " + str(e))

def send_email(change, email=None):
    try:
        admins = User.query.filter_by(user_group='administrator', notification=True).all()
        emails = []
        for admin in admins:
            emails.append(admin.email)
        if email is not None:
            user = getUserByEmail(email=email)
            if user.user_group != 'administrator' and user.notification:
                emails.append(user.email)
        msg = Message('Vacation Management',
                      sender='noreply@demo.com',
                      recipients=emails)
        msg.body = f'''There has been a change:
            {change}
        If you would like to turn off the notifications visit your account settings!'''
        send_async_email(app, msg)
    except SyntaxError as e:
        logging.error("Error " + str(e))
