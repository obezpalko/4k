"""
main programm.
"""

import json
from decimal import Decimal
from datetime import date
from flask import Flask, request, url_for, redirect, session, \
    render_template, Response
# from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy_session import flask_scoped_session
from sqlalchemy import func, and_, select
from .oauth import GOOGLE, REDIRECT_URI, get_user_info
from .database import DB_URL, DB_SESSION, User, \
    UserCurrencies, Currency, Account, Rate, Transaction, \
    DBJsonEncoder
from .utils import strip_numbers

__version__ = "1.0.1"

APP = Flask(__name__)  # create the application instance :)
APP.config.from_object(__name__)  # load config from this file , flaskr.py
DB = flask_scoped_session(DB_SESSION, APP)
SECRET = 'icDauKnydnomWovijOakgewvIgyivfahudWocnelkikAndeezCogneftyeljogdy'

# Load default config and override config from an environment variable
APP.config.update(dict(
    SECRET_KEY=SECRET,
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
    if exc is None:
        pass
    DB_SESSION.remove()


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
    return GOOGLE.authorize(callback=callback)


@APP.route(REDIRECT_URI)
@GOOGLE.authorized_handler
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
            gender=userinfo['gender'] if 'gender' in userinfo else None,
            link=userinfo['link'] if 'link' in userinfo else None,
            picture=userinfo['picture'] if 'picture' in userinfo else None
        )
        DB.add(user)
        DB.commit()
    return user.user_id


@GOOGLE.tokengetter
def get_access_token():
    """ return session token """
    return session.get('access_token')


@APP.route('/logout')
def logout():
    """ log user out and clear session """
    session.pop('user', '')
    return redirect(url_for('index'))  # , _external=True, _scheme='https'))


@APP.route('/accounts')
def accounts():
    """ show account page """
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template(
        "accounts.html",
        accounts=DB.query(Account).filter(
            and_(
                Account.user_id == session['user'][0],
                Account.deleted != True
            )
            ).order_by(Account.title, Account.currency_id).all(),
        user=DB.query(User).get(session['user'][0])
    )


@APP.route('/currency')
def currency():
    ''' show currency page '''
    if 'user' not in session:
        return redirect(url_for('index'))
    subq = DB.query(UserCurrencies).filter(
        UserCurrencies.user_id == session['user'][0]).subquery('userq')
    currencies = DB.query(Currency, subq).outerjoin(
        subq, subq.c.currency_id == Currency.record_id).order_by(
            Currency.name).all()
    return render_template(
        "currency.html",
        currencies=currencies,
        user=DB.query(User).get(session['user'][0])
    )


def currency_get(**kwargs):
    '''
    get list of currency rates
    '''
    max_date_q = select([
        Rate.currency_b_id.label("b_id"),
        func.max(Rate.rate_date).label("rate_date")]).group_by(
            Rate.currency_b_id).alias('max_date_q')
    rates_query = DB.query(
        Rate.currency_b_id, Rate, Rate.rate_date
    ).join(
        max_date_q,
        and_(
            max_date_q.c.b_id == Rate.currency_b_id,
            max_date_q.c.rate_date == Rate.rate_date
        )
    )

    entries = []
    if 'id' in kwargs and kwargs['id']:
        try:
            return rates_query.filter(
                Rate.currency_b_id == kwargs['id']).first()[1].json
        except TypeError:
            return []
    else:
        for rate in rates_query.all():
            entries.append(rate[1].json)
    return entries


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
            ).update(
                {UserCurrencies.default: False},
                synchronize_session='evaluate')
        updated = DB.query(UserCurrencies).filter(
            and_(
                UserCurrencies.user_id == session['user'][0],
                UserCurrencies.currency_id == kwargs['id']
                )
            ).update(
                {UserCurrencies.default: True},
                synchronize_session='evaluate')
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
    return {'result': 'Ok'}


def usercurrency_delete(**kwargs):
    ''' delete user currency '''
    DB.query(UserCurrencies).filter(
        and_(
            UserCurrencies.user_id == session['user'][0],
            UserCurrencies.currency_id == kwargs['id'])
        ).delete(synchronize_session=False)
    DB.commit()
    return {'result': 'Ok'}


def account_post(**kwargs):
    ''' update account '''
    obj = json.loads(request.data.decode('utf-8', 'strict'))
    account = account = DB.query(Account).get(kwargs['id'])
    if 'visible' in obj:
        account.visible = obj['visible']
    if 'title' in obj:
        account.title = obj['title']
    if 'currency' in obj:
        account.currency_id = obj['currency']
    if 'balance' in obj:
        delta_summ = Decimal(strip_numbers(obj['balance'])) - account.balance()
        if delta_summ != 0:
            print('summ update required')
            transaction = Transaction(
                time=date.today(), summ=delta_summ,
                account_id=kwargs['id'], user_id=session['user'][0],
                comment='fix account summ')
            DB.add(transaction)
    DB.commit()
    return {'result': 'Ok'}


def account_put(**kwargs):
    ''' update account '''
    obj = json.loads(request.data.decode('utf-8', 'strict'))
    new_account = Account(
        title=obj['title'],
        currency_id=obj['currency'],
        user_id=session['user'][0],
        visible=obj['visible']
    )
    DB.add(new_account)
    if 'balance' in obj:
        DB.flush()
        new_account.fix_balance(Decimal(obj['balance']))
    print("kwargs: {}".format(kwargs))
    DB.commit()

    return {'result': 'Ok', 'id': new_account.record_id}


def account_get(**kwargs):
    ''' account api '''
    if kwargs['id'] == 0:
        return {
            "id": 0,
            "title": "",
            "currency": {"id": 1},
            "balance": 0.00,
            "visible": True,
            "deleted": False
        }
    return DB.query(Account).filter(
        and_(
            Account.record_id == kwargs['id'],
            Account.user_id == session['user'][0]
        )).first()


def account_delete(**kwargs):
    ''' mark account as deleted if there are transactions '''
    account = DB.query(Account).get(kwargs['id'])
    if DB.query(Transaction).filter(Transaction.account_id == kwargs['id']).count() > 0:
        account.deleted = True
        account.show = False
    else:
        DB.query(Account).filter(Account.record_id == kwargs['id']).delete()
    DB.commit()
    return {'deleted': kwargs['id']}


@APP.route(
    '/api/<string:api>',
    defaults={'id': 0},
    methods=['GET', 'POST', 'PUT'])
@APP.route(
    '/api/<string:api>/<int:id>',
    methods=['GET', 'DELETE', 'PUT', 'POST'])
def main_dispatcher(**kwargs):
    """ main dispatcher """
    if 'user' not in session:
        return '{"access": "denied"}'

    return Response(
        response=json.dumps(
            globals()["{}_{}".format(
                kwargs['api'],
                str(request.method).lower())](**kwargs),
            cls=DBJsonEncoder
            ),
        status=200,
        mimetype="application/json")
