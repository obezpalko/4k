"""
main programm
"""
# all the imports
import os
import http.client
import json
import csv
import datetime
import decimal
from flask import Flask, request, session, redirect, url_for, \
    render_template, flash

from sqlalchemy import func, and_, or_
from .utils import number_of_weeks
from .income import DB, Currency, Rate, Income, Interval, Transaction, Account, Payforward

app = Flask(__name__)  # create the application instance :)
app.config.from_object(__name__)  # load config from this file , flaskr.py

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'e4.db'),
    SECRET_KEY='icDauKnydnomWovijOakgewvIgyivfahudWocnelkikAndeezCogneftyeljogdy',
    USERNAME='admin',
    PASSWORD='NieniarcEgHiacHeulijkikej',
    HORIZON='12m',
    SQLALCHEMY_DATABASE_URI='sqlite:///e4.db'
))
app.config.from_envvar('E4_SETTINGS', silent=True)


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    if isinstance(obj, (Currency, Income, Rate, Interval, Transaction, Account)):
        return obj.to_dict()
    if isinstance(obj, decimal.Decimal):
        return format(obj.__str__())
    raise TypeError("Type {} not serializable ({})".format(type(obj), obj))


@app.cli.command('rates')
@app.route('/update_rates')
def update_rates():
    default_currency = DB.query(Currency).filter_by(default=1).first()
    conn = http.client.HTTPConnection('download.finance.yahoo.com', 80)
    param = []
    c_title = {}
    for currency in DB.query(Currency).all():
        param.append("{}{}=X".format(currency, default_currency))
        c_title[currency.title] = currency.id
    cmd = "http://download.finance.yahoo.com/d/quotes.csv?f=sl1d1t1&s={}".format(
        ','.join(param))
    conn.request("GET", cmd)

    param = []
    objects = []
    results = conn.getresponse().read().decode("utf-8", "strict")

    for row in csv.reader(results.split('\n'), delimiter=',', quoting=csv.QUOTE_NONNUMERIC):
        if len(row) < 1:
            continue

        objects.append(
            Rate(
                rate_date=datetime.datetime.strptime(
                    "{} {}".format(
                        row[2], row[3]),
                    "%m/%d/%Y %I:%M%p"),
                currency_a=default_currency.id,
                currency_b=c_title[row[0].replace(
                    '{}=X'.format(default_currency.title), '')],
                rate=row[1]))
    DB.bulk_save_objects(objects)
    DB.commit()

    try:
        if request.method == 'GET':
            return redirect(url_for('dispatcher', api='currency'))
        return True
    except RuntimeError:
        return True


@app.route('/')
@app.route('/incomes')
@app.route('/income')
def show_incomes():
    return render_template('show_entries.html',
                           entries=list(map(lambda x: x.to_dict(), income_get(id=0))),
                           currencies=currency_get(id=0),
                           periods=intervals_get(id=0),
                           transactions=list(map(lambda x: x.to_dict(), transaction_get(id=0))))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_incomes'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

#
def currency_get(**kwargs):
    entries = []
    if 'id' in kwargs and kwargs['id']:
        try:
            rate = DB.query(Rate.currency_b, Rate, func.max(Rate.rate_date)).filter_by(
                currency_b=kwargs['id']).group_by(Rate.currency_b).first()
            return rate[1].to_dict()
        except TypeError:
            return {}
    else:
        rates = DB.query(
            Rate.currency_b, Rate, func.max(Rate.rate_date)).group_by(Rate.currency_b).all()
        for rate in rates:
            entries.append(rate[1].to_dict())
    return entries

#
def income_delete(**kwargs):
    DB.query(Income).filter_by(id=kwargs['id']).delete()
    DB.commit()
    return {'deleted': kwargs['id']}


def income_get(**kwargs):
    return DB.query(Income).all() if kwargs['id'] == 0 else DB.query(Income).get(kwargs['id'])


def income_post(**kwargs):
    obj = json.loads(request.data.decode('utf-8', 'strict'))
    # try:
    i = Income(
        title=obj['title'],
        currency_id=int(obj['currency.id']),
        sum=decimal.Decimal(obj['sum']),
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


def income_put(**kwargs):
    i = DB.query(Income).get(kwargs['id'])

    obj = json.loads(request.data.decode('utf-8', 'strict'))
    # try:
    i.title = obj['title']
    i.currency_id = int(obj['currency.id'])
    i.sum = decimal.Decimal(obj['sum'])
    i.start_date = datetime.datetime.strptime(
        obj['start_date'], '%Y-%m-%d').date()
    i.end_date = (None if obj['end_date'] == '' else datetime.datetime.strptime(
        obj['end_date'], '%Y-%m-%d').date())
    i.period_id = int(obj['period.id'])
    # except:
    #    abort(400)
    DB.commit()
    return {'updated': DB.query(Income).get(kwargs['id']), "previous": i}

#
def account_get(**kwargs):
    if kwargs['id'] == 0:
        return DB.query(Account).filter(Account.deleted == 'n').all()
    else:
        return DB.query(Account).get(kwargs['id'])


def account_delete(**kwargs):
    income = DB.query(Account).get(kwargs['id'])
    if DB.query(Transaction).filter(Transaction.account_id == kwargs['id']).count() > 0:
        income.deleted = 'y'
        income.show = 'n'
    else:
        DB.query(Account).filter(Account.id == kwargs['id']).delete()
    DB.commit()
    return {'deleted': kwargs['id']}


def account_post(**kwargs):
    """ add new account and set first transaction with rests of money """
    obj = json.loads(request.data.decode('utf-8', 'strict'))
    new_account = Account(title=obj['title'], currency_id=int(obj['currency.id']))
    DB.add(new_account)
    DB.flush()
    if float(obj['sum']) > 0:
        DB.add(Transaction(account_id=new_account.id,
                           show=obj['show'],
                           comment='initial summ',
                           time=datetime.date.today(),
                           sum=obj['sum']))
    DB.commit()
    return new_account


def account_put(**kwargs):
    a = DB.query(Account).get(kwargs['id'])
    obj = json.loads(request.data.decode('utf-8', 'strict'))
    a.title = obj['title']
    a.show = obj['show']
    a.currency_id = obj['currency.id']
    delta_sum = decimal.Decimal(obj['sum']) - a.sum()
    if delta_sum != 0:
        t = Transaction(time=datetime.date.today(), sum=delta_sum,
                        account_id=kwargs['id'], comment='fix account summ')
        DB.add(t)
    DB.commit()
    return {'updated': DB.query(Account).get(kwargs['id']), "previous": a}

#
def transaction_delete(**kwargs):
    income = DB.query(Transaction).filter_by(id=kwargs['id']).delete()
    DB.query(Payforward).filter_by(transaction_id=kwargs['id']).delete()
    DB.commit()
    return {'deleted': income}


def transaction_get(**kwargs):
    """ load intervals from database """
    if kwargs['id'] == 0:
        return DB.query(Transaction).order_by(Transaction.time).all()
    else:
        return DB.query(Transaction).order_by(Transaction.time).get(kwargs['id'])


def transaction_post(**kwargs):
    obj = json.loads(request.data.decode('utf-8', 'strict'))
    # try:
    i = Transaction(
        time=datetime.datetime.strptime(obj['time'], '%Y-%m-%d').date(),
        account_id=int(obj['account.id']),
        sum=decimal.Decimal(obj['sum']),
        transfer=int(obj['transfer']),
        income_id=int(obj['income.id']),
        comment=obj['comment']
    )
    DB.add(i)
    DB.flush()
    DB.commit()
    # except:
    #    abort(400)
    return i


def transaction_put(**kwargs):
    i = DB.query(Transaction).get(kwargs['id'])
    obj = json.loads(request.data.decode('utf-8', 'strict'))
    # try:
    i.time = datetime.datetime.strptime(obj['time'], '%Y-%m-%d').date()
    i.account_id = int(obj['account.id']) if obj['account.id'] != '' else None
    i.sum = decimal.Decimal(obj['sum'])
    i.transfer = int(obj['transfer']) if obj['transfer'] not in [
        '0', ''] else None
    i.income_id = int(obj['income.id']) if obj['income.id'] not in [
        '0', ''] else None
    i.comment = obj['comment']
    # except:
    #    abort(400)
    DB.commit()
    return {'updated': DB.query(Transaction).get(kwargs['id']), "previous": i}

#
def balance_get(**kwargs):
    r = {}
    incomes = DB.query(Income).all()

    for i in incomes:
        s = i.get_sum(start_date=kwargs['start_date'],
                      end_date=kwargs['end_date'])
        try:
            r[i.currency.title] += s
        except KeyError:
            r[i.currency.title] = s
    total = 0
    for c in currency_get():
        if c['title'] in r:
            total += decimal.Decimal(c['rate'] * r[c['title']])
            r[c['title']] = r[c['title']]
    r['TOTAL'] = int(total)
    r['start_date'] = kwargs['start_date']
    r['end_date'] = kwargs['end_date']
    w = number_of_weeks(kwargs['start_date'].strftime(
        '%Y-%m-%d'), kwargs['end_date'].strftime('%Y-%m-%d'))
    r['weeks'] = w
    today = datetime.date.today()
    week_begin = today - datetime.timedelta(today.isoweekday() % 7) # sunday
    week_end = week_begin + datetime.timedelta(7)
    # print(week_begin, week_end)
    week_sum = decimal.Decimal(0)
    tmp_results = DB.query(Transaction).join(Account).join(Currency).filter(
        and_(or_(Transaction.income_id <= 0, Transaction.income_id is None),
             and_(Transaction.sum < 0,
                  and_(Transaction.time >= week_begin, Transaction.time < week_end)
                 )
            )).all()

    for k in tmp_results:
        #print(t)
        week_sum += k.sum*k.account.currency.get_rate().rate

    r['weekly'] = "{}/{}".format(int(-1*week_sum), r['TOTAL'] // w)
    return r

#
def backlog_get(**kwargs):
    results = []
    week_ahead = datetime.date.today() \
        - datetime.timedelta(datetime.date.today().isoweekday() % 7)\
        + datetime.timedelta(14)
    if kwargs['id'] > 0:
        return income_get(id=kwargs['id'], end_date=week_ahead).get_backlog()
    for i in list(map(lambda x: x.get_backlog(), income_get(id=0, end_date=week_ahead))):
        for k in i:
            results.append(k)
    return sorted(results, key=lambda x: x['time'], reverse=True)


def backlog_delete(**kwargs):
    # just create transaction with sum zero
    obj = json.loads(request.data.decode('utf-8', 'strict'))
    t = Transaction(
        time=datetime.datetime.strptime(obj['origin_time'], '%Y-%m-%d').date(),
        account_id=0,
        sum=0,
        income_id=obj['income.id'],
        comment='cancelled')
    DB.add(t)
    DB.flush()
    DB.commit()
    return t


def backlog_put(**kwargs):
    # actually insert transaction
    obj = json.loads(request.data.decode('utf-8', 'strict'))
    origin_time = datetime.datetime.strptime(obj['origin_time'], '%Y-%m-%d').date()
    operation_time = datetime.datetime.strptime(obj['time'], '%Y-%m-%d').date()

    t = Transaction(
        time=operation_time,
        account_id=int(obj['account.id']),
        sum=obj['sum'],
        income_id=obj['income.id'],
        comment=obj['comment'])
    DB.add(t)
    DB.flush()
    if origin_time > operation_time:
        # payment before
        DB.add(
            Payforward(
                income_id=int(obj['income.id']),
                income_date=origin_time,
                payment_date=operation_time,
                transaction_id=t.id
            )
        )
    DB.commit()
    return t


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
                "incomes": income_get()
            }
           }


s_date = datetime.date.today()


@app.route('/api', defaults={'api': 'balance'}, methods=['GET'])
@app.route('/api/<string:api>', defaults={'id': 0}, methods=['GET', 'POST'])
@app.route('/api/<string:api>/<int:id>',
           defaults={'end_date': s_date.replace(year=(s_date.year + 1))},
           methods=['GET', 'DELETE', 'PUT'])
@app.route('/api/<string:api>/<int:id>/<string:end_date>',
           defaults={'start_date': s_date - datetime.timedelta(s_date.isoweekday() % 7)},
           methods=['GET'])
@app.route('/api/<string:api>/<int:id>/<string:start_date>/<string:end_date>', methods=['GET'])
def dispatcher(**kwargs):
    """ main dispatcher """
    if 'start_date' in kwargs and isinstance(kwargs['start_date'], datetime.date):
        start_date = kwargs['start_date']
    else:
        try:
            start_date = datetime.datetime.strptime(
                kwargs['start_date'], '%Y-%m-%d').date()
        except (ValueError, KeyError):
            start_date = datetime.date.today()
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
