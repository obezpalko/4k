"""
main programm
"""

# import uuid
# from datetime import datetime, timedelta
from flask import Flask, url_for, redirect, session
# from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy_session import flask_scoped_session
from .oauth import google, REDIRECT_URI, get_user_info
from .database import DB_URL, db_session, User


__version__ = "1.0"

app = Flask(__name__)  # create the application instance :)
app.config.from_object(__name__)  # load config from this file , flaskr.py
DB = flask_scoped_session(db_session, app)

# Load default config and override config from an environment variable
app.config.update(dict(
    SECRET_KEY='icDauKnydnomWovijOakgewvIgyivfahudWocnelkikAndeezCogneftyeljogdy',
    PREFERRED_URL_SCHEME='http',
    SESSION_TYPE='sqlalchemy',
    SQLALCHEMY_DATABASE_URI=DB_URL,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    DEBUG=True
))

app.config.from_envvar('E4_SETTINGS', silent=True)


@app.teardown_appcontext
def shutdown_session():
    db_session.remove()


@app.route('/')
def index():
    # sess = Session.query.first()
    # return "user {}".format(dir(session))
    if 'user' in session:
        return "userid: \n{}".format(
            session['user'])
    return redirect(url_for('login'))

@app.route('/login')
def login():
    callback = url_for('authorized', _external=True)
    return google.authorize(callback=callback)

@app.route(REDIRECT_URI)
@google.authorized_handler
def authorized(resp):
    access_token = resp['access_token']
    userinfo = get_user_info(access_token)
    session['user'] = check_user(userinfo), ''
    return redirect(url_for('index'))

def check_user(userinfo):
    user = DB.query(User).filter_by(email=userinfo['email']).first()
    if user is None:
        user = User(
            email=userinfo['email'],
            name=userinfo['name'],
            gender=userinfo['gender'],
            link=userinfo['link'],
            picture=userinfo['picture']
        )
        DB.add(user)
        DB.commit()
    return user.user_id

@google.tokengetter
def get_access_token():
    # return "access_token"
    return session.get('access_token')

@app.route('/logout')
def logout():
    # session.pop('logged_in', None)
    # session.pop('access_token', None)
    session.pop('user', '')
    return redirect(url_for('index')) #  , _external=True, _scheme='https'))
