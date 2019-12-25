"""
main programm
"""
# all the imports
import os
import json
import re
import datetime
import decimal
from flask import Flask, request, session, redirect, url_for, \
    render_template, flash, send_file, make_response
from functools import wraps
from flask_dance.contrib.google import make_google_blueprint, google

#  from flask_login import UserMixin, login_required, login_user, logout_user, current_user
# from flask_oauth import OAuth
# from flask_sqlalchemy import SQLAlchemy
from urllib3 import PoolManager
import certifi
from sqlalchemy import func, and_, or_, desc, select
from .utils import number_of_weeks, strip_numbers
from .database import DB, DB_URL, Currency, Rate, Income, Interval, Transaction, Account, Payforward
# from .income import DB, Currency, Rate, Income, Interval, Transaction, \
#     Account, Payforward
#  from .plot import plot_weekly_plan

__version__ = "0.4.1"

RE_C_EXCHANGE = re.compile(
    r'<div id=currency_converter_result>1 (?P<currency_b>[A-Z]{3}) ='
    ' <span class=bld>(?P<rate>[0-9.]*) (?P<currency_a>[A-Z]{3})</span>')


app = Flask(__name__)  # create the application instance :)
app.config.from_object(__name__)  # load config from this file , flaskr.py
app.debug = True

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', default=False)
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', default=False)
# REDIRECT_URI = '/oauth2callback'  # one of the Redirect URIs from Google APIs console

# oauth = OAuth()

# google = oauth.remote_app(
#     'google',
#     base_url='https://www.google.com/accounts/',
#     authorize_url='https://accounts.google.com/o/oauth2/auth',
#     request_token_url=None,
#     request_token_params={'scope': 'https://www.googleapis.com/auth/userinfo.email',
#                           'response_type': 'code'},
#     access_token_url='https://accounts.google.com/o/oauth2/token',
#     access_token_method='POST',
#     access_token_params={'grant_type': 'authorization_code'},
#     consumer_key=GOOGLE_CLIENT_ID,
#     consumer_secret=GOOGLE_CLIENT_SECRET)


#
# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'e4.db'),
    SECRET_KEY=os.environ.get('APP_SECRET_KEY', default=False),
    USERNAME=os.environ.get('APP_USERNAME', default=False),
    PASSWORD=os.environ.get('APP_PASSWORD', default=False),
    HORIZON='12m',
    PREFERRED_URL_SCHEME='https',
    SESSION_TYPE='sqlalchemy',
    SQLALCHEMY_DATABASE_URI=DB_URL,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    DEBUG=True
))
app.config.from_envvar('E4_SETTINGS', silent=True)
blueprint = None
blueprint = make_google_blueprint(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email"
        ]
)
app.register_blueprint(blueprint, url_prefix="/login")


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    if isinstance(obj, (Currency, Income, Rate, Interval, Transaction, Account)):
        return obj.to_dict()
    if isinstance(obj, decimal.Decimal):
        return format(obj.__str__())
    raise TypeError("Type {} not serializable ({})".format(type(obj), obj))


class IsAuthorized(object):
    """ decorator """
    def __init__(self, f):
        self.f = f
    def __call__(self, *args, **kwargs):
        self.f(*args, **kwargs)


def is_authorized(a_func):
    @wraps(a_func)
    def wrapTheFunc(*args, **kwargs):
        if not google.authorized:
            return redirect(url_for("google.login"))
        if not session.get('logged_in', False):
            resp = google.get("/oauth2/v1/userinfo")
            assert resp.ok, resp.text
            if not (resp.json()['email'] in ['alex@bezpalko.mobi', 'obezpalko@gmail.com']):
                return redirect(url_for('google.login'))
            session['email'] = resp.json()['email']
            session['logged_in'] = True
        return a_func(*args, **kwargs)
    return wrapTheFunc

@app.teardown_request
def session_clear(exception=None):
    #  Session.remove()
    if exception:
        DB.rollback()

@app.cli.command('rates')
@app.route('/update_rates')
def update_rates():
    default_currency = DB.query(Currency).filter_by(default=1).first()
    http = PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
    c_title = {}
    objects = []
    for currency in DB.query(Currency).all():
        if currency == default_currency:
            continue
        c_title[currency.title] = currency.record_id
        _request = http.request(
            'GET',
            "https://finance.google.com/finance/converter?a=1&from={}&to={}".format(
                currency, default_currency))
        if _request.status == 200:
            for line in _request.data.decode('utf-8', 'replace').split('\n'):
                if "id=currency_converter_result" in line:
                    match = RE_C_EXCHANGE.match(line)
                    if match:
                        print("{} {} {}".format(match.group('currency_a'),
                                                match.group('currency_b'),
                                                match.group('rate')))
                        objects.append(
                            Rate(
                                rate_date=datetime.datetime.now(),
                                currency_a_id=default_currency.record_id,
                                currency_b_id=c_title[match.group('currency_b')],
                                rate=match.group('rate')))

        else:
            print("cannot get rate {}:{} ({})".format(
                currency,
                default_currency,
                _request.status))

    DB.bulk_save_objects(objects)
    DB.commit()
    try:
        if request.method == 'GET':
            return redirect(url_for('dispatcher', api='currency', _external=True, _scheme='https'))
        return True
    except (RuntimeError, AttributeError):
        return True

@app.route('/')
@app.route('/incomes')
@is_authorized
def show_incomes():
    """
    docstring here
    """

    return render_template('show_entries.html',
                           entries=list(map(lambda x: x.to_dict(), incomes_get(id=0))),
                           currencies=currency_get(id=0),
                           periods=intervals_get(id=0),
                           transactions=list(map(lambda x: x.to_dict(), transactions_get(id=0))))



# @google.tokengetter
def get_access_token():
    app.logger.info('token getter')
    return session.get('access_token')


@app.route('/logout')
def logout():
    app.logger.info('logout')
    resp = make_response(redirect(url_for('show_incomes', _external=True, _scheme='https')))
    resp.set_cookie('session', '', max_age=0)
    return resp


@app.cli.command('version')
def version_get():
    return {'version': __version__}


def currency_get(**kwargs):
    '''
    get list of currency rates
    '''
    max_date_q = select([
        Rate.currency_b_id.label("b_id"),
        func.max(Rate.rate_date).label("rate_date")
    ]).group_by(Rate.currency_b_id ).alias('max_date_q')
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
            return rates_query.filter(Rate.currency_b_id == kwargs['id']).first()[1].to_dict()
        except TypeError:
            return []
    else:
        for rate in rates_query.all():
            entries.append(rate[1].to_dict())
    return entries


def incomes_delete(**kwargs):
    DB.query(Income).filter_by(id=kwargs['id']).delete()
    DB.commit()
    return {'deleted': kwargs['id']}


def incomes_get(**kwargs):
    return DB.query(Income).all() if kwargs['id'] == 0 else DB.query(Income).get(kwargs['id'])


def incomes_post(**kwargs):
    obj = json.loads(request.data.decode('utf-8', 'strict'))
    # try:
    i = Income(
        title=obj['title'],
        currency_id=int(obj['currency.id']),
        sum=decimal.Decimal(strip_numbers(obj['sum'])),
        start_date=datetime.datetime.strptime(
            obj['start_date'], '%Y-%m-%d').date(),
        end_date=(None if obj['end_date'] == '' else datetime.datetime.strptime(
            obj['end_date'], '%Y-%m-%d').date()),
        period_id=int(obj['period.id'])
    )
    DB.add(i)
    DB.flush()
    DB.commit()
    # except:
    #    abort(400)
    return i


def incomes_put(**kwargs):
    i = DB.query(Income).get(kwargs['id'])

    obj = json.loads(request.data.decode('utf-8', 'strict'))
    # try:
    i.title = obj['title']
    i.currency_id = int(obj['currency.id'])
    i.sum = decimal.Decimal(strip_numbers(obj['sum']))
    i.start_date = datetime.datetime.strptime(
        obj['start_date'], '%Y-%m-%d').date()
    i.end_date = (None if obj['end_date'] == '' else datetime.datetime.strptime(
        obj['end_date'], '%Y-%m-%d').date())
    i.period_id = int(obj['period.id'])
    # except:
    #    abort(400)
    DB.commit()
    return {'updated': DB.query(Income).get(kwargs['id']), "previous": i}


def accounts_get(**kwargs):
    if kwargs['id'] == 0:
        return DB.query(Account).filter(Account.deleted == 'n').order_by(Account.title).all()
    return DB.query(Account).get(kwargs['id'])


def accounts_delete(**kwargs):
    income = DB.query(Account).get(kwargs['id'])
    if DB.query(Transaction).filter(Transaction.account_id == kwargs['id']).count() > 0:
        income.deleted = 'y'
        income.show = 'n'
    else:
        DB.query(Account).filter(Account.record_id == kwargs['id']).delete()
    DB.commit()
    return {'deleted': kwargs['id']}


def accounts_post(**kwargs):
    """ add new account and set first transaction with rests of money """
    obj = json.loads(request.data.decode('utf-8', 'strict'))
    new_account = Account(title=obj['title'], currency_id=int(obj['currency.id']))
    DB.add(new_account)
    DB.flush()
    if float(strip_numbers(obj['sum'])) > 0:
        DB.add(Transaction(account_id=new_account.id,
                           show=obj['show'],
                           comment='initial summ',
                           time=datetime.date.today(),
                           sum=strip_numbers(obj['sum'])))
    DB.commit()
    return new_account


def accounts_put(**kwargs):
    a = DB.query(Account).get(kwargs['id'])
    obj = json.loads(request.data.decode('utf-8', 'strict'))
    a.title = obj['title']
    a.show = obj['show']
    a.currency_id = obj['currency.id']
    delta_sum = decimal.Decimal(strip_numbers(obj['sum'])) - a.sum()
    if delta_sum != 0:
        t = Transaction(time=datetime.date.today(), sum=delta_sum,
                        account_id=kwargs['id'], comment='fix account summ')
        DB.add(t)
    DB.commit()
    return {'updated': DB.query(Account).get(kwargs['id']), "previous": a}


def transactions_delete(**kwargs):
    income = DB.query(Transaction).filter_by(record_id=kwargs['id']).delete()
    DB.query(Payforward).filter_by(transaction_id=kwargs['id']).delete()
    DB.commit()
    return {'deleted': income}


def transactions_get(**kwargs):
    """ load intervals from database """
    if kwargs['id'] == 0:
        return DB.query(Transaction).order_by(
            #  desc(Transaction.time)).limit(100).from_self().order_by(
            desc(Transaction.time)).filter(
                Transaction.time>=((
                    datetime.date.today().replace(day=1) -
                    datetime.timedelta(1)
                ).replace(day=1) - datetime.timedelta(1)).replace(day=1)
            ).from_self().order_by(
                Transaction.time).all()
    return DB.query(Transaction).order_by(
        desc(Transaction.time)).get(kwargs['id'])


def transactions_post(**kwargs):
    obj = json.loads(request.data.decode('utf-8', 'strict'))
    # try:
    i = Transaction(
        time=datetime.datetime.strptime(obj['time'], '%Y-%m-%d').date(),
        account_id=int(obj['account.id']) if int(obj['account.id']) > 0 else None,
        sum=decimal.Decimal(strip_numbers(obj['sum'])),
        transfer=int(obj['transfer']) if int(obj['transfer']) > 0 else None,
        income_id=int(obj['income.id']) if int(obj['income.id']) > 0 else None,
        comment=obj['comment']
    )
    DB.add(i)
    DB.flush()
    if 'new_account.id' in obj:
        transfer = Transaction(
            time=datetime.datetime.strptime(obj['time'], '%Y-%m-%d').date(),
            account_id=int(obj['new_account.id']) if int(obj['new_account.id']) > 0 else None,
            sum=decimal.Decimal(strip_numbers(obj['new_sum'])),
            transfer=int(obj['transfer']) if int(obj['transfer']) > 0 else None,
            income_id=int(obj['income.id']) if int(obj['income.id']) > 0 else None,
            comment=obj['comment']
        )
        DB.add(transfer)
        DB.flush()
        i.transfer = transfer.record_id
        transfer.transfer = i.record_id
    DB.commit()
    # except:
    #    abort(400)
    return i


def transactions_put(**kwargs):
    i = DB.query(Transaction).get(kwargs['id'])
    obj = json.loads(request.data.decode('utf-8', 'strict'))
    # try:
    i.time = datetime.datetime.strptime(obj['time'], '%Y-%m-%d').date()
    i.account_id = int(obj['account.id']) if obj['account.id'] != '' else None
    i.sum = decimal.Decimal(strip_numbers(obj['sum']))
    i.transfer = int(obj['transfer']) if obj['transfer'] not in [
        '0', ''] else None
    i.income_id = int(obj['income.id']) if obj['income.id'] not in [
        '0', ''] else None
    i.comment = obj['comment']
    # except:
    #    abort(400)
    DB.commit()
    return {'updated': DB.query(Transaction).get(kwargs['id']), "previous": i}


def balance_get(**kwargs):
    """
    return balance forecast for dates
    """
    balance = {}
    incomes = DB.query(Income).filter(
        and_(Income.start_date <= kwargs['end_date'],
             or_(Income.end_date >= kwargs['start_date'], Income.end_date == None)))
    for i in incomes.all():
        _sum = i.get_sum(start_date=kwargs['start_date'],
                         end_date=kwargs['end_date'],
                         ignore_pf=True)
        try:
            balance[i.currency.title] += _sum
        except KeyError:
            balance[i.currency.title] = _sum
    total = 0
    for currency in currency_get():
        if currency['title'] in balance:
            total += decimal.Decimal(currency['rate'] * balance[currency['title']])
            balance[currency['title']] = balance[currency['title']]
    balance['TOTAL'] = int(total)
    balance['start_date'] = kwargs['start_date']
    balance['end_date'] = kwargs['end_date']
    balance['weeks'] = number_of_weeks(
        kwargs['start_date'].strftime('%Y-%m-%d'),
        kwargs['end_date'].strftime('%Y-%m-%d'))
    today = datetime.date.today()
    week_begin = today - datetime.timedelta(today.isoweekday() % 7)  # sunday
    week_end = week_begin + datetime.timedelta(7)
    week_sum = decimal.Decimal(0)
    tmp_results = DB.query(Transaction).join(Account).join(Currency).filter(
        and_(or_(Transaction.transfer == None, Transaction.transfer <= 0),
             and_(or_(Transaction.income_id <= 0, Transaction.income_id == None),
                  and_(Transaction.sum < 0,
                       and_(Transaction.time >= week_begin, Transaction.time < week_end)
                      )
                 )
            )).all()

    for k in tmp_results:
        week_sum += k.sum * k.account.currency.get_rate().rate

    balance['weekly'] = "{}/{}".format(int(-1*week_sum), balance['TOTAL'] // balance['weeks'])
    return balance


def backlogs_get(**kwargs):
    results = []
    week_ahead = datetime.date.today() \
        - datetime.timedelta(datetime.date.today().isoweekday() % 7)\
        + datetime.timedelta(14)
    if kwargs['id'] > 0:
        return incomes_get(id=kwargs['id'], end_date=week_ahead).get_backlog()
    for i in list(map(lambda x: x.get_backlog(), incomes_get(id=0, end_date=week_ahead))):
        for k in i:
            results.append(k)
    return sorted(results, key=lambda x: x['time'], reverse=True)


def backlogs_delete(**kwargs):
    # just create transaction with sum zero
    obj = json.loads(request.data.decode('utf-8', 'strict'))
    t = Transaction(
        time=datetime.datetime.strptime(obj['origin_time'], '%Y-%m-%d').date(),
        account_id=None,
        sum=0,
        income_id=int(obj['income.id']) if int(obj['income.id']) > 0 else None,
        comment='cancelled')
    DB.add(t)
    DB.flush()
    DB.commit()
    return t


def backlogs_put(**kwargs):
    """
    actually insert transaction
    """
    obj = json.loads(request.data.decode('utf-8', 'strict'))
    origin_time = datetime.datetime.strptime(obj['origin_time'], '%Y-%m-%d').date()
    operation_time = datetime.datetime.strptime(obj['time'], '%Y-%m-%d').date()

    transaction = Transaction(
        time=operation_time,
        account_id=int(obj['account.id']) if int(obj['account.id']) > 0 else None,
        sum=strip_numbers(obj['sum']),
        income_id=int(obj['income.id']) if int(obj['income.id']) > 0 else None,
        comment=obj['comment'])
    DB.add(transaction)
    DB.flush()
    if origin_time != operation_time:
        # payment before
        DB.add(
            Payforward(
                income_id=int(obj['income.id']),
                income_date=origin_time,
                payment_date=operation_time,
                transaction_id=transaction.record_id
            )
        )
    DB.commit()
    return transaction


def intervals_get(**kwargs):
    """ load intervals from database """
    return DB.query(Interval).all() if kwargs['id'] == 0 else DB.query(Interval).get(kwargs['id'])


def plan_get(**kwargs):
    if 'start' in kwargs:
        start_date = kwargs['start']
    else:
        start_date = datetime.datetime.now().strftime("%Y-%m-%d")
    if 'horizon' in kwargs:
        horizon = kwargs['horizon']
    else:
        horizon = app.config['HORIZON']
    return {'plan':
            {
                "start": start_date,
                "horizon": horizon,
                "intervals": intervals_get(),
                "currencies": currency_get(),
                "incomes": incomes_get()
            }
           }



@app.route('/api', defaults={'api': 'balance'}, methods=['GET'])
@app.route('/api/<string:api>', defaults={'id': 0}, methods=['GET', 'POST'])
@app.route('/api/<string:api>/<int:id>',
           defaults={
               'end_date': datetime.date.today().replace(
                   year=(datetime.date.today().year + 1))
           },
           methods=['GET', 'DELETE', 'PUT'])
@app.route('/api/<string:api>/<int:id>/<string:end_date>',
           defaults={
               'start_date': datetime.date.today() - datetime.timedelta(
                   datetime.date.today().isoweekday() % 7)
           },
           methods=['GET'])
@app.route('/api/<string:api>/<int:id>/<string:start_date>/<string:end_date>', methods=['GET'])
@is_authorized
def dispatcher(**kwargs):
    """ main dispatcher """

    if 'start_date' in kwargs and isinstance(kwargs['start_date'], datetime.date):
        start_date = kwargs['start_date']
    else:
        try:
            start_date = datetime.datetime.strptime(
                kwargs['start_date'], '%Y-%m-%d').date()
        except (ValueError, KeyError):
            start_date = datetime.date.today() - datetime.timedelta(
                datetime.date.today().isoweekday() % 7)
    if 'end_date' in kwargs and isinstance(kwargs['end_date'], datetime.date):
        end_date = kwargs['end_date']
    else:
        try:
            end_date = datetime.datetime.strptime(
                kwargs['end_date'], '%Y-%m-%d').date()
        except (ValueError, KeyError):
            end_date = datetime.datetime.now().replace(
                year=datetime.datetime.now().year + 1).date()
    kwargs.update({'start_date': start_date, 'end_date': end_date})
    return json.dumps(globals()["{}_{}".format(
        kwargs['api'],
        str(request.method).lower())](**kwargs), default=json_serial)


@app.route('/img/<string:plot>/<string:start_date>/<string:end_date>', methods=['GET'])
def plot_graph(**kwargs):
    """
    docstring here
        :param **kwargs:
    """
    return send_file(
        globals()["plot_{}".format(kwargs['plot'])](**kwargs),
        'image/png')


if __name__ == '__main__':
    app.run()
