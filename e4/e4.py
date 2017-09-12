# all the imports
import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
import http.client
import json

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
    cur = db.execute('select currency_id, currency_index, is_default from currency where is_default == 1 limit 1')
    default_currency = cur.fetchall()[0]
    print("default currency: {}".format(default_currency['currency_index']))
    cur = db.execute('select currency_id, currency_index, is_default from currency')
    conn = http.client.HTTPConnection('download.finance.yahoo.com', 80)

    for currency in cur.fetchall():
        conn.request("GET", "http://download.finance.yahoo.com/d/quotes.csv?e=.csv&f=sl1d1t1&s={}{}=X".format(
                    currency['currency_index'], default_currency['currency_index']))
        r1=conn.getresponse()
        rate = float(str(r1.read()).split(",")[1])
        cur = db.execute('insert into rates values(date("now"), ?, ?, ?)', (default_currency['currency_id'], currency['currency_id'], rate))
        print("cur.lastrowid {}".format(cur.lastrowid))
        print("currency {} rate: {}".format(currency['currency_index'], rate))
    db.commit()
    # db.close()
    try:
        if request.method == 'GET':
            return json.dumps(get_currencies([]))
        return True
    except RuntimeError:
        return True

@app.route('/')
def show_default():
    db = get_db()
    cur = db.execute('select id, title from incomes order by id desc')
    entries = cur.fetchall()
    return render_template('show_entries.html', entries=entries)

@app.route('/incomes')
def show_incomes():
    db = get_db()
    cur = db.execute('''
    select
        incomes.id as id,
        incomes.title as title,
        incomes.sum as sum,
        currency.currency_index as currency,
        currency.currency_id as currency_id,
        intervals.title as period,
        intervals.id as interval,
        incomes.start_date as start,
        incomes.end_date as end
    from
        incomes,
        currency,
        intervals
    where
        currency.currency_id = incomes.currency
        and
        intervals.id = incomes.period
    order by id desc
    ''')
    entries = cur.fetchall()
    return render_template('show_entries.html',
        entries=entries,
        currencies=get_currencies(),
        periods=load_intervals1())
    

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
        distinct currency.currency_id,
        currency.currency_index,
        rates.rate,
        max(rates.rate_date) as rate_date,
        currency.is_default
    from currency, rates
    where rates.currency_b = currency.currency_id 
    {}
    group by currency.currency_index
    order by currency.currency_index
    """.format(
        "and currency.currency_id in ({})".format(
            ','.join(map(str, currency_ids))) if len(currency_ids)>0 else ""))
    entries = cur.fetchall()
    dat = {}
    for d in entries:
        dat[int(d['currency_id'])] = d
    return dat

@app.route('/c')
def show_currencies():
    return render_template('show_currencies.html', entries=get_currencies())


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

@app.route('/api', defaults={'api': 'balance'}, methods=['GET'])
@app.route('/api/<path:api>', methods=['GET', 'POST', 'PUT', 'DELETE', 'UPDATE'])
def dispatcher(api):
    # result = "{}".format(globals()["{}_{}".format(api, request.method)]())
    result = globals()["{}_{}".format(api, request.method)]([])
    
    return json.dumps(result)

