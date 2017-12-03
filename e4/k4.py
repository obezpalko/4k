"""
main programm
"""

import json
# from datetime import datetime, timedelta
from flask import Flask, request, url_for, redirect, session, \
    render_template
# from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy_session import flask_scoped_session
from sqlalchemy import and_
from .oauth import google, REDIRECT_URI, get_user_info
from .database import DB_URL, db_session, User, \
    UserCurrencies, Currency, Account

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


@APP.route('/accounts')
def accounts():
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template(
        "accounts.html",
        accounts=DB.query(Account).filter(UserCurrencies.user_id == session['user'][0]).order_by(Account.title).all(),
        user=DB.query(User).get(session['user'][0])
    )


@APP.route('/currency')
def currency():
    if 'user' not in session:
        return redirect(url_for('index'))
    subq = DB.query(UserCurrencies).filter(
        UserCurrencies.user_id == session['user'][0]).subquery('userq')
    currencies = DB.query(Currency, subq).outerjoin(
        subq, subq.c.currency_id == Currency.record_id).order_by(Currency.name).all()
    return render_template(
        "currency.html",
        currencies=currencies,
        user=DB.query(User).get(session['user'][0])
    )


def usercurrency_put(**kwargs):
    """ update user currencies

    Arguments:
        **kwargs id -- currency id

    Returns:
        json -- result code
    """

    obj = json.loads(request.data.decode('utf-8', 'strict'))
    updated = 0

    if 'default' in obj and obj['default']:
        # clean previous default
        updated = DB.query(UserCurrencies).filter(
            and_(
                UserCurrencies.user_id == session['user'][0],
                UserCurrencies.currency_id != kwargs['id'])
            ).update({UserCurrencies.default: False}, synchronize_session='evaluate')
        updated = DB.query(UserCurrencies).filter(
            and_(
                UserCurrencies.user_id == session['user'][0],
                UserCurrencies.currency_id == kwargs['id']
                )
            ).update({UserCurrencies.default: True}, synchronize_session='evaluate')
        if updated == 0:
            # if not updated nothing - inser new record
            DB.add(UserCurrencies(
                user_id=session['user'][0],
                currency_id=kwargs['id'],
                default=True
                ))
    else:
        DB.add(UserCurrencies(
            user_id=session['user'][0],
            currency_id=kwargs['id']
            ))
    DB.commit()
    return json.dumps({'result': 'Ok'})

def usercurrency_delete(**kwargs):
    DB.query(UserCurrencies).filter(
        and_(
            UserCurrencies.user_id == session['user'][0],
            UserCurrencies.currency_id == kwargs['id'])
        ).delete(synchronize_session=False)
    DB.commit()
    return json.dumps({'result': 'Ok'})


def account_post(**kwargs):
    obj = json.loads(request.data.decode('utf-8', 'strict'))
    update = {}
    print("obj: {}".format(obj))
    if 'edit' in obj:
        if 'visible' in obj['edit']:
            update[Account.visible] = obj['edit']['visible']
        DB.query(Account).filter(
            and_(
                Account.record_id == kwargs['id'],
                Account.user_id == session['user'][0]
            )).update(update, synchronize_session='evaluate')
        DB.commit()
        return json.dumps({'result': 'Ok'})

@APP.route('/api/<string:api>', defaults={'id': 0}, methods=['GET', 'POST'])
@APP.route('/api/<string:api>/<int:id>', methods=['GET', 'DELETE', 'PUT', 'POST'])
def main_dispatcher(**kwargs):
    """ main dispatcher """
    if 'user' not in session:
        return '{"access": "denied"}'
    return json.dumps(
        globals()["{}_{}".format(
            kwargs['api'],
            str(request.method).lower())](**kwargs)
        )