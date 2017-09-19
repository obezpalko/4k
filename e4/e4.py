# all the imports
import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash, Response
# from flask_sqlalchemy import SQLAlchemy
import http.client
import json
import csv
from .utils import *
from .income import DB, Currency, Rate, Income, Interval, Transaction, Account, CURRENCY_SCALE
import datetime

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, func


app = Flask(__name__) # create the application instance :)
app.config.from_object(__name__) # load config from this file , flaskr.py

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
    raise TypeError("Type %s not serializable" % type(obj))


#@app.teardown_appcontext
#def close_db(error):
#    """Closes the database again at the end of the request."""
#    if hasattr(g, 'sqlite_db'):
#       g.sqlite_db.close()


#@app.cli.command('initdb')
#def initdb_command():
#    """Initializes the database."""
#    init_db()
#    print('Initialized the database.')


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
        # print(default_currency, default_currency.id, default_currency.title)
        # print(c_title[row[0].replace(
        #    '{}=X'.format(default_currency.title), '')])
        objects.append(Rate(rate_date=datetime.datetime.strptime("{} {}".format(row[2], row[3]), "%m/%d/%Y %I:%M%p"),
                            currency_a=default_currency.id,
                            currency_b=c_title[row[0].replace(
                                '{}=X'.format(default_currency.title), '')],
                            rate=float(row[1])))
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
    # list(map(lambda x: x.to_dict() ,i))
    return render_template('show_entries.html',
                           entries=list(map(lambda x: x.to_dict(), income_GET(id=0))),
                           currencies=currency_GET(id=0),
                           periods=intervals_GET(id=0),
                           transactions=list(map(lambda x: x.to_dict(), transaction_GET(id=0)))
                           )


@app.route('/income/modify', methods=['POST'])
def add_entry():

    if not session.get('logged_in'):
        abort(401)
    try:
        current_income = DB.query(Income).get(int(request.form['hidden_id']))
        current_income.title = request.form['title']
        current_income.currency_id = int(request.form['currency'])
        current_income.sum = int(request.form['sum']*CURRENCY_SCALE)
        current_income.start_date = datetime.datetime.strptime(
            request.form['start_date'], '%Y-%m-%d').date()
        current_income.end_date = (None if request.form['end_date'] == '' else atetime.datetime.strptime(
            request.form['end_date'], '%Y-%m-%d').date())
        current_income.period_id = int(request.form['period'])

    except:
        current_income = Income(
            id=int(request.form['period']),
            title=request.form['title'],
            currency_id=int(request.form['currency']),
            sum=inf(request.form['sum']*CURRENCY_SCALE),
            start_date=datetime.datetime.strptime(
                request.form['start_date'], '%Y-%m-%d').date(),
            end_date=(None if request.form['end_date'] == '' else atetime.datetime.strptime(
                request.form['end_date'], '%Y-%m-%d').date()),
            period_id=int(request.form['period']))
        DB.add(current_income)

    DB.commit()
    #flash('New entry was successfully posted')
    return redirect(url_for('show_incomes'))


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


def currency_GET(*args, **kwargs):
    entries = []
    if 'id' in kwargs and kwargs['id']:
        try:
            q, rate, l = DB.query(Rate.currency_b, Rate, func.max(Rate.rate_date)).filter_by(
                currency_b=kwargs['id']).group_by(Rate.currency_b).first()
            return rate.to_dict()
        except TypeError:
            return {}
    else:
        for currency_id, rate, rate_date in DB.query(Rate.currency_b, Rate, func.max(Rate.rate_date)).group_by(Rate.currency_b).all():
            entries.append(rate.to_dict())
    return entries


def income_GET(*args, **kwargs):
    data = DB.query(Income).all() if kwargs['id'] == 0 else DB.query(Income).get(kwargs['id'])
    return data


def income_DELETE(*args, **kwargs):
    id = kwargs['id']
    income = DB.query(Income).filter_by(id=id).delete()
    DB.commit()
    return {'deleted': id}


incomes_GET = income_GET


def income_PUT(*args, **kwargs):
    id = kwargs['id']
    i = DB.query(Income).get(id)
    
    obj=json.loads(request.data.decode('utf-8', 'strict'))
    try:
        i.title=obj['title']
        i.currency_id=int(obj['currency_id'])
        i.sum=int(obj['sum']*CURRENCY_SCALE)
        i.start_date=datetime.datetime.strptime( obj['start_date'], '%Y-%m-%d').date()
        i.end_date=(None if obj['end_date']=='' else datetime.datetime.strptime( obj['end_date'], '%Y-%m-%d').date())
        i.period_id=int(obj['period_id'])
    except:
        abort(400)
    DB.commit()
    return {'updated': DB.query(Income).get(id), "previous": i}


def income_POST(*args, **kwargs):
    id = kwargs['id']
    obj=json.loads(request.data.decode('utf-8', 'strict'))
    try:    
        i=Income(
            title=obj['title'],
            currency_id=int(obj['currency_id']),
            sum=int(obj['sum']*CURRENCY_SCALE),
            start_date=datetime.datetime.strptime( obj['start_date'], '%Y-%m-%d').date(),
            end_date=(None if obj['end_date']=='' else datetime.datetime.strptime( obj['end_date'], '%Y-%m-%d').date()),
            period_id=int(obj['period_id'])
        )
        DB.add(i)
        DB.flush()
        DB.commit()
    except:
        abort(400)
    return i

def transaction_POST(*args, **kwargs):
    id = kwargs['id']
    obj=json.loads(request.data.decode('utf-8', 'strict'))
    print(obj)
    try:    
        i=Transaction(
            time=datetime.datetime.strptime( obj['time'], '%Y-%m-%d').date(),
            account_id=int(obj['account_id']),
            sum=int(obj['sum']*CURRENCY_SCALE),
            transfer=int(obj['transfer']),
            income_id=int(obj['income_id']),
            comment=obj['comment']
        )
        DB.add(i)
        DB.flush()
        DB.commit()
    except:
        abort(400)
    return i

def transaction_PUT(*args, **kwargs):
    id = kwargs['id']
    i = DB.query(Transaction).get(id)

    obj=json.loads(request.data.decode('utf-8', 'strict'))
    print(obj)
    #try:
    i.time=datetime.datetime.strptime( obj['time'], '%Y-%m-%d').date()
    i.account_id=int(obj['account_id']) if obj['account_id'] != '' else None
    i.sum=int(float(obj['sum'])*CURRENCY_SCALE)
    i.transfer=int(obj['transfer']) if obj['transfer'] != '' else None
    i.income_id=int(obj['income_id']) if obj['income_id'] != '' else None
    i.comment=obj['comment']
    #except:
    #    abort(400)
    DB.commit()
    return {'updated': DB.query(Transaction).get(id), "previous": i}

def transaction_GET(*args, **kwargs):
    """ load intervals from database """
    return DB.query(Transaction).all() if kwargs['id'] == 0 else DB.query(Transaction).get(kwargs['id'])

def transaction_DELETE(*args, **kwargs):
    id = kwargs['id']
    income = DB.query(Transaction).filter_by(id=id).delete()
    DB.commit()
    return {'deleted': id}

def balance_GET(*args, **kwargs):
    r = {}
    incomes = DB.query(Income).all()
    for i in incomes:
        s = i.get_sum(start_date=kwargs['start_date'],
                      end_date=kwargs['end_date'])[2]
        try:
            r[i.currency.title] += s/CURRENCY_SCALE
        except KeyError:
            r[i.currency.title] = s/CURRENCY_SCALE
    total = 0
    for c in currency_GET():
        if c['title'] in r:
            total += c['rate'] * r[c['title']]
    r['TOTAL'] = '{:.2f}'.format(total)
    r['start_date'] = kwargs['start_date']
    r['end_date'] = kwargs['end_date']
    w = number_of_weeks(kwargs['start_date'].strftime('%Y-%m-%d'), kwargs['end_date'].strftime('%Y-%m-%d'))
    r['weeks'] = w
    r['weekly'] = float('{:.2}'.format(total/w))
    return r


def intervals_GET(*args, **kwargs):
    """ load intervals from database """
    return DB.query(Interval).all() if kwargs['id'] == 0 else DB.query(Interval).get(kwargs['id'])


def account_GET(*args, **kwargs):
    """ load intervals from database """
    return DB.query(Account).all() if kwargs['id'] == 0 else DB.query(Account).get(kwargs['id'])


def plan_GET(*args, **kwargs):
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
                "intervals": intervals_GET(),
                "currencies": currency_GET(),
                "incomes": income_GET()
            }
            }

def transactions_GET(*args, **kwargs):
    return kwargs, args


defaults = {
        'id': 0,
        'start_date': '1970-01-01',
        'end_date': '9999-12-31',
        'account': 0
        }
methods=['GET']
s_date=datetime.date.today()
@app.route('/api', defaults={'api': 'balance'}, methods=methods)
@app.route('/api/<string:api>', defaults={'id': 0}, methods=['GET', 'POST'])
@app.route('/api/<string:api>/<int:id>', defaults={'end_date': s_date.replace(year=(s_date.year+1))}, methods=['GET', 'DELETE', 'PUT'])
@app.route('/api/<string:api>/<int:id>/<string:end_date>', defaults={'start_date': s_date.isoformat()}, methods=methods)
@app.route('/api/<string:api>/<int:id>/<string:start_date>/<string:end_date>', methods=methods)
def dispatcher(*args, **kwargs):
    
    # print(args, kwargs)
    try:
        start_date = datetime.datetime.strptime(kwargs['start_date'], '%Y-%m-%d').date()
    except:
        start_date = datetime.date.today()
    try:
        end_date = datetime.datetime.strptime(kwargs['end_date'], '%Y-%m-%d').date()
    except:
        end_date = datetime.datetime.now().replace(year=datetime.datetime.now().year+1).date()
    kwargs.update({'start_date': start_date, 'end_date': end_date})
    return json.dumps(globals()["{}_{}".format(kwargs['api'], request.method)](*args, **kwargs), default=json_serial)
