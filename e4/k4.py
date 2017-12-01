"""
main programm
"""

import json
# from datetime import datetime, timedelta
from flask import Flask, request, url_for, redirect, session, \
    render_template
# from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy_session import flask_scoped_session
from sqlalchemy import and_, exc
from .oauth import google, REDIRECT_URI, get_user_info
from .database import DB_URL, db_session, User, \
    UserCurrencies, Currency

__version__ = "1.0.1"

APP = Flask(__name__)  # create the application instance :)
APP.config.from_object(__name__)  # load config from this file , flaskr.py
DB = flask_scoped_session(db_session, APP)

# Load default config and override config from an environment variable
APP.config.update(dict(
    SECRET_KEY='icDauKnydnomWovijOakgewvIgyivfahudWocnelkikAndeezCogneftyeljogdy',
    PREFERRED_URL_SCHEME='http',
    SESSION_TYPE='sqlalchemy',
    SQLALCHEMY_DATABASE_URI=DB_URL,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    DEBUG=True
))

APP.config.from_envvar('E4_SETTINGS', silent=True)


@APP.teardown_appcontext
def shutdown_session(exc=None):
    """ clean database session on errors """
    print("{}".format(exc))
    db_session.remove()


@APP.route('/')
def index():
    """
    index page
    """
    user = None
    if 'user' in session:
        user = DB.query(User).get(session['user'][0])
    return render_template("index.html", user=user)


@APP.route('/login')
def login():
    """ login hook """
    callback = url_for('authorized', _external=True)
    return google.authorize(callback=callback)


@APP.route(REDIRECT_URI)
@google.authorized_handler
def authorized(resp):
    """ authorize user from google """
    access_token = resp['access_token']
    userinfo = get_user_info(access_token)
    session['user'] = check_user(userinfo), ''
    return redirect(url_for('index'))


def check_user(userinfo):
    """ check if user exists and crete if not """
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
    """ return session token """
    return session.get('access_token')


@APP.route('/logout')
def logout():
    """ log user out and clear session """
    session.pop('user', '')
    return redirect(url_for('index')) #  , _external=True, _scheme='https'))

@APP.route('/currency')
def currency():
    if 'user' not in session:
        return redirect(url_for('index'))
    subq = DB.query(UserCurrencies).filter(
        UserCurrencies.user_id == session['user'][0]).subquery('userq')
    currencies = DB.query(Currency, subq).outerjoin(subq, subq.c.currency_id == Currency.record_id).all()
    return render_template(
        "currency.html",
        # my_currencies=DB.query(UserCurrencies).filter_by(user_id=session['user'][0]).all(),
        currencies=currencies,
        user=DB.query(User).get(session['user'][0])
    )

@APP.route('/currency/set/default', methods=['PUT'])
def set_default_currency():
    if 'user' not in session:
        return '{"access": "denied"}'
    # delete if default already exists
    obj = json.loads(request.data.decode('utf-8', 'strict'))
    updated = DB.query(UserCurrencies).filter(
        and_(
            UserCurrencies.user_id == session['user'][0],
            UserCurrencies.currency_id != obj['currency_id'])
        ).update({UserCurrencies.default: False}, synchronize_session=False)
    updated = DB.query(UserCurrencies).filter(
        and_(
            UserCurrencies.user_id == session['user'][0],
            UserCurrencies.currency_id == obj['currency_id'])
        ).update({UserCurrencies.default: True}, synchronize_session=False)
    if updated == 0:
        temp_user = UserCurrencies(
            user_id=session['user'][0],
            currency_id=obj['currency_id'],
            default=True)
        DB.add(temp_user)
    DB.commit()
    return '{"result": "Ok"}'

@APP.route('/currency/<int:currency_id>', methods=['POST','DELETE'])
def update_user_currency(**kwargs):
    if 'user' not in session:
        return '{"access": "denied"}'
    if str(request.method).lower() == 'delete':
        DB.query(UserCurrencies).filter(
            and_(
                UserCurrencies.user_id == session['user'][0],
                UserCurrencies.currency_id == kwargs['currency_id'])
            ).delete(synchronize_session=False)
    else:
        tmp_user = UserCurrencies(
            user_id=session['user'][0],
            currency_id=kwargs['currency_id']
        )
        DB.add(tmp_user)
    DB.commit()
    return '{"result": "Ok"}'