# all the imports
import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash
# from flask_sqlalchemy import SQLAlchemy
import http.client
import json
import csv
from .utils import *
from .income import DB, Currency, Rate, Income, Interval, Transaction, Account
import datetime

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, func


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
    # if obj.__class__.__name__ in  ['Currency']:
    if isinstance(obj, (Currency, Income, Rate, Interval, Transaction, Account)):
        return obj.to_dict()
    raise TypeError("Type %s not serializable" % type(obj))


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print('Initialized the database.')


@app.cli.command('rates')
@app.route('/update_rates')
def update_rates():
    # db = get_db()
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
    for row in csv.reader(conn.getresponse().read().decode("utf-8", "strict").split('\n'), delimiter=',', quoting=csv.QUOTE_NONNUMERIC):
        if len(row) < 1:
            continue
        print(default_currency, default_currency.id, default_currency.title)
        print(c_title[row[0].replace(
            '{}=X'.format(default_currency.title), '')])
        objects.append(Rate(rate_date=datetime.datetime.strptime("{} {}".format(row[2], row[3]), "%m/%d/%Y %I:%M%p"),
                            currency_a=default_currency.id,
                            currency_b=c_title[row[0].replace(
                                '{}=X'.format(default_currency.title), '')],
                            rate=float(row[1])))
    DB.bulk_save_objects(objects)

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
                           entries=income_GET().values(),
                           currencies=currency_GET(),
                           periods=intervals_GET(),
                           transactions=transaction_GET()
                           )


@app.route('/income/modify', methods=['POST'])
def add_entry():

    if not session.get('logged_in'):
        abort(401)
    try:
        current_income = DB.query(Income).get(int(request.form['hidden_id']))
        current_income.title = request.form['title']
        current_income.currency_id = int(request.form['currency'])
        current_income.sum = float(request.form['sum'])
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
            sum=float(request.form['sum']),
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
    entries = {}
    for e in DB.query(Income).all():
        entries.update(e.to_dict())
    return entries


def income_DELETE(*args, **kwargs):
    id = request.form['id']
    income = DB.query(Income).filter_by(id=int(id)).delete()
    DB.commit()
    return {'deleted': id}


incomes_GET = income_GET


def transaction_GET(*args, **kwargs):
    return DB.query(Transaction).all()


def balance_GET(*args, **kwargs):
    r = {}
    if 'end_date' in kwargs:
        e = kwargs['end_date']
    incomes = DB.query(Income).all()
    for i in incomes:
        s = i.get_sum(start_date=kwargs['start_date'],
                      end_date=kwargs['end_date'])[2]
        try:
            r[i.currency.title] += s
        except KeyError:
            r[i.currency.title] = s
    total = 0
    for c in currency_GET():
        if c['title'] in r:
            total += c['rate'] * r[c['title']]
    r['<br/>TOTAL'] = float('{:10.2f}'.format(total))

    return r


def intervals_GET(*args, **kwargs):
    """ load intervals from database """
    return DB.query(Interval).all() if ('id' not in kwargs or kwargs['id'] == None) else DB.query(Interval).get(int(kwargs['id']))


def account_GET(*args, **kwargs):
    """ load intervals from database """
    return DB.query(Account).all() if kwargs['id'] == None else DB.query(Account).get(int(kwargs['id']))


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


@app.route('/api', defaults={'api': 'balance'}, methods=['GET'])
@app.route('/api/<string:api>', methods=['GET', 'POST', 'PUT', 'DELETE', 'UPDATE'], defaults={'id': None})
@app.route('/api/<string:api>/<int:id>', methods=['GET', 'POST', 'PUT', 'DELETE', 'UPDATE'])
def dispatcher(api, id=None):
    return json.dumps(globals()["{}_{}".format(api, request.method)](id=id), default=json_serial)


@app.route('/api/balance/<string:start_date>/<string:end_date>', defaults={'api': 'balance'}, methods=['GET'])
@app.route('/api/balance/<string:end_date>', defaults={'api': 'balance', 'start_date': datetime.date.today().strftime("%Y-%m-%d")}, methods=['GET'])
def balance(api, start_date, end_date):
    return json.dumps(globals()["{}_{}".format(api, request.method)](start_date=datetime.datetime.strptime(start_date, '%Y-%m-%d').date(),
                                                                     end_date=datetime.datetime.strptime(end_date, '%Y-%m-%d').date()), default=json_serial)
