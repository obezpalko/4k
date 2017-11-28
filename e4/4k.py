"""
main programm
"""

from flask_sqlalchemy import SQLAlchemy
from flask import Flask, url_for, session, redirect
from .oauth import google, REDIRECT_URI, get_user_info
from sqlalchemy.orm.session import Session
from flask_session import Session

__version__ = "1.0"

app = Flask(__name__)  # create the application instance :)
app.config.from_object(__name__)  # load config from this file , flaskr.py

DB_URL = 'postgresql://e4:og8ozJoch\Olt6@localhost:5432/e4-dev'

# Load default config and override config from an environment variable
app.config.update(dict(
    SECRET_KEY='icDauKnydnomWovijOakgewvIgyivfahudWocnelkikAndeezCogneftyeljogdy',
    PREFERRED_URL_SCHEME='https',
    SESSION_TYPE = 'sqlalchemy',
    SQLALCHEMY_DATABASE_URI = DB_URL,
    SQLALCHEMY_TRACK_MODIFICATIONS = False,
    DEBUG=True
))

app.config.from_envvar('E4_SETTINGS', silent=True)
db = SQLAlchemy(app)
sess = Session()
sess.init_app(app)


class Session(db.Model):
    __tablename__ = 'sessions'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String, unique=True)
    data = db.Column(db.LargeBinary)
    expiry = db.Column(db.DateTime)

    def __init__(self, session_id, data, expiry):
        self.session_id = session_id
        self.data = data
        self.expiry = expiry

    def __repr__(self):
        return '<Session data %s>' % self.data
'''
class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True, name='id')
    email = db.Column(db.String, unique=True, nullable=False)
    username = db.Column(db.String, nullable=False)
    gender = db.Column(db.String, nullable=True)
    link = db.Column(db.String, nullable=True)
    picture = db.Column(db.String, nullable=True)

    def __repr__(self):
        return '<User %r>' % self.username
'''
db.create_all()




@app.route('/')
def show_all():
    if 'access_token' in session:
        return "{}\n{}".format(
            session['access_token'],
            session['userinfo'])
    return "Ok"

@app.route('/login')
def login():
    callback = url_for('authorized', _external=True)
    return google.authorize(callback=callback)

@app.route(REDIRECT_URI)
@google.authorized_handler
def authorized(resp):
    access_token = resp['access_token']
    session['access_token'] = access_token, ''
    userinfo = get_user_info(access_token)
    session['userinfo'] = userinfo, ''
    #  s = User()
    #  s.email=userinfo['email']
    #  s.username=userinfo['name']
    #  db.session.add(s)
    #  db.session.commit()
    return redirect(url_for('show_all'))

@google.tokengetter
def get_access_token():
    return session.get('access_token')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('access_token', None)
    session.pop('email', '')
    return redirect(url_for('show_all')) #  , _external=True, _scheme='https'))

