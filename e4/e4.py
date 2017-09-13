# all the imports
import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
import http.client
import json
import csv

app = Flask(__name__) # create the application instance :)
app.config.from_object(__name__) # load config from this file , flaskr.py

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'e4.db'),
    SECRET_KEY='icDauKnydnomWovijOakgewvIgyivfahudWocnelkikAndeezCogneftyeljogdy',
    USERNAME='admin',
    PASSWORD='NieniarcEgHiacHeulijkikej'
))
app.config.from_envvar('E4_SETTINGS', silent=True)

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def to_dict(a=[], id_="id"):
    result = {}
    for row in a:
        result[row[id_]] = row
    return result

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.execute("PRAGMA foreign_keys = 1")
    #rv.row_factory = sqlite3.Row
    rv.row_factory = dict_factory
    return rv

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    
def load_intervals1():
    """ load intervals from database """
    db = get_db()
    cur = db.execute('select id, title, item, value from intervals order by id desc')
    entries = cur.fetchall()
    return entries

@app.cli.command('show_intervals1')
def show_intervals1():
    for r in load_intervals1():
        print(r['id'])

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
    db = get_db()
    cur = db.execute('select id, "index", "default" from currency where "default" == 1 limit 1')
    default_currency = cur.fetchall()[0]
    cur = db.execute('select id, "index", "default" from currency')
    conn = http.client.HTTPConnection('download.finance.yahoo.com', 80)
    param = []
    c_index = {}
    for currency in cur.fetchall():
        param.append("{}{}=X".format(currency['index'], default_currency['index']))
        c_index[currency['index']] = currency['id']
    cmd = "http://download.finance.yahoo.com/d/quotes.csv?f=sl1d1&s={}".format(','.join(param))
    conn.request("GET", cmd)
    param = []
    
    for row in csv.reader(conn.getresponse().read().decode("utf-8", "strict").split('\n'), delimiter=',', quoting=csv.QUOTE_NONNUMERIC):
        if len(row) < 1: continue
        param.append(
            (
                default_currency['id'],
                c_index[row[0].replace('{}=X'.format(default_currency['index']), '')],
                float(row[1])
            )
        )
    cur = db.executemany(
        'insert into rates ("rate_date", "currency_a", "currency_b", "rate") values (datetime("now"), ?, ?, ?)',
        param
        )
    db.commit()
    try:
        if request.method == 'GET':
            return json.dumps(to_dict(get_currencies([])))
        return True
    except RuntimeError:
        return True


@app.route('/')
@app.route('/incomes')
@app.route('/income')

def show_incomes():
    return render_template('show_entries.html',
        entries=get_incomes(),
        currencies=get_currencies(),
        periods=load_intervals1())
    
def get_incomes(*args, **kwargs):
    db = get_db()
    cur = db.execute('''
    select
        incomes.id as id,
        incomes.title as title,
        incomes.sum as sum,
        currency."index" as currency,
        currency.id as currency_id,
        intervals.title as period,
        intervals.id as interval,
        incomes.start_date as start,
        incomes.end_date as end
    from
        incomes,
        currency,
        intervals
    where
        currency.id = incomes.currency
        and
        intervals.id = incomes.period
    order by id desc
    ''')
    entries = cur.fetchall()
    return entries
    
    

@app.route('/intervals')
def load_intervals():
    """ load intervals from database """
    db = get_db()
    cur = db.execute('select id, title, item, value from intervals order by id desc')
    entries = cur.fetchall()
    return render_template('show_intervals.html', entries=entries)

def get_currencies(currency_ids=[]):
    db = get_db()
    cur = db.execute("""
    select 
        distinct currency.id,
        currency."index",
        rates.rate,
        max(rates.rate_date) as rate_date,
        currency."default"
    from currency, rates
    where rates.currency_b = currency.id 
    {}
    group by currency."index"
    order by currency."index"
    """.format(
        "and currency.id in ({})".format(
            ','.join(map(str, currency_ids))) if len(currency_ids)>0 else ""))
    entries = cur.fetchall()
    return entries


@app.route('/income/modify', methods=['POST'])
def add_entry():
    
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    parameters = [request.form['title'], 
                int(request.form['currency']),
                float(request.form['sum']),
                request.form['start_date'],
                request.form['end_date'],
                int(request.form['period'])
                ]
    if request.form['submit'] == 'Insert':
        cmd = 'insert into incomes (title, currency, sum, start_date, end_date, period) values (?, ?, ?, ?, ?, ?)'
    else:
        cmd = "update incomes set title = ?, currency = ?, sum = ?, start_date = ?, end_date = ?, period = ? where id = ?"
        parameters.append(int(request.form['hidden_id']))
    # open('/tmp/debug','w').write("{}".format(request.form))
    db.execute( cmd, parameters)
    db.commit()
    flash('New entry was successfully posted')
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

def currency_GET(param):
    return get_currencies(param)

def income_GET(*args, **kwargs):
    return get_incomes(*args, **kwargs)

@app.route('/api', defaults={'api': 'balance'}, methods=['GET'])
@app.route('/api/<path:api>', methods=['GET', 'POST', 'PUT', 'DELETE', 'UPDATE'])
def dispatcher(api):
    return json.dumps(to_dict(globals()["{}_{}".format(api, request.method)]([])))

