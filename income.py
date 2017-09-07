#!/usr/local/bin/python3
"""
income class
"""
from datetime import datetime, date, time, timedelta
from calendar import monthrange
from pprint import pprint
from uuid import uuid4
import yaml
import csv
import money
import http.client
import os.path
from time import time

default_currency = 'ILS'

def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = int(sourcedate.year + month / 12)
    month = month % 12 + 1
    day = min(sourcedate.day, monthrange(year, month)[1])
    return sourcedate.replace(year, month, day)


intervals = {
    'daily': 1,
    'weekly': 7,
    'biweekly': 14,
    'monthly': 1,
    'bimonthly': 2,
    'quaterly': 3,
    'half-year': 6,
    'yearly': 12
}


def refresh_rates(base_currency, update_currencies=[]):
    r_file = 'rates.yml'
    try:
        r=yaml.load(open(r_file))
        force_update = False
    except FileNotFoundError:
        r = {base_currency:{}}
        force_update = True
    if force_update or time() - os.path.getmtime(r_file) > 86400:
        c_set = set()
        for c in update_currencies:
            c_set.add(c)
        for c in r[base_currency]:
            c_set.add(c)
        conn = http.client.HTTPConnection('download.finance.yahoo.com', 80)

        for c in c_set:
            conn.request("GET", "http://download.finance.yahoo.com/d/quotes.csv?e=.csv&f=sl1d1t1&s={}{}=X".format(
                    c, base_currency))
            r1=conn.getresponse()
            r[base_currency][c] = float(str(r1.read()).split(",")[1])
        conn.close()
        yaml.dump(r, open(r_file,'w'), explicit_start=True, explicit_end=True)
    return r[base_currency]


def next_date(current_date, period, count=1):
    if period in ['daily', 'weekly', 'biweekly']:
        return current_date + timedelta(intervals[period] * count)
    else:
        return add_months(current_date, intervals[period] * count)


class Income(object):
    """ """

    def __init__(self, summ, start_date, end_date=None, period='monthly', id=str(uuid4()), name=None, currency=default_currency):
        object.__init__(self)
        self.summ = summ
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            self.end_date = end_date
        self.period = period
        if id == '~' or id == null:
            self.id=str(uuid4())
        else:
            self.id = id
        pprint(self.id)
        self.name = name
        self.currency = currencey

    def __repr__(self):
        return "from {} sum {} {} till {} {}".format(
            self.start_date,
            self.summ,
            self.period,
            self.end_date,
            self.currency
        )
    def fix_id(self):
        if self.id is None:
            self.id=str(uuid4())

    def get_dates(self, start_date=datetime.now(), end_date=datetime.now()):
        list_dates = []
        s = 0
        _sd = max(start_date, self.start_date)
        if self.end_date:
            _ed = min(end_date, self.end_date)
        else:
            _ed = end_date
        if _sd > _ed:
            return []
        if _sd == self.start_date:
           s = self.summ
           list_dates.append((self.name, _sd, s, self.currency))
        # pprint ("{} {} {}".format(self.start_date, _sd, _ed))
        #if _sd < self.start_date:
        #    list_dates.append((self.name, _sd, s, self.currency))
        nd = next_date(self.start_date, self.period)
        while nd <= _ed:
            if nd >= _sd and nd <= _ed:
                s += self.summ
                list_dates.append((self.name, nd, s, self.currency))
            nd = next_date(nd, self.period)
        return list_dates
    
    def get_sum(self, start_date=datetime.now(), end_date=datetime.now()):
        try:
            return self.get_dates(start_date, end_date)[-1]
        except IndexError:
            return (self.name, None, 0, self.currency)

class Balance(object):
    def __init__(self, incomes=[]):
        object.__init__(self)
        self.incomes = incomes
        self.current_rates = refresh_rates(default_currency, self._get_currencies())
    def _get_currencies(self):
        c = set()
        for i in self.incomes:
            c.add(i.currency)
        return c
    def _totals(self, start=datetime.now(), end=datetime.now()):
        t = {"_{}".format(default_currency): 0}
        s = 0
        for c in self._get_currencies():
            t[c] = 0
        for i in self.incomes:
            (name, st, bal, curr) = i.get_sum(start, end)
            t[curr] += bal
            if default_currency == curr:
                t["_{}".format(default_currency)] += bal
            else:
                t["_{}".format(default_currency)] += bal * self.current_rates[curr]
        return t
    
class Transaction(object):
    def __init__(self,id=uuid4(), income_reference=None, income_date=None, income_summ = None, real_date=None, real_summ=None):
        object.__init__(self)
        if id == '~':
            self.id=str(uuid4())
        else:
            self.id = id
        self.income_reference = income_reference
        self.income_date = income_date
        self.income_summ = income_summ
        if real_date:
            self.real_date = real_date
        else:
            self.real_date = self.income_date
        if real_summ:
            self.real_summ = real_summ
        else:
            self.real_summ = self.income_summ
    def __repr__(self):
        return "{};{};{};{};{};{}".format(
            self.id,
            self.income_reference,
            self.income_date,
            self.income_summ,
            self.real_date,
            self.real_summ)
        
class Transactions(object):
    def __init__(self, file_name):
        object.__init__(self)
        self.file_name = file_name
        self.transactions = []
        self._load()
    def _load(self):
        
        for row in csv.reader(open(self.file_name, 'r'), delimiter=';'):
            self.transactions.append(Transaction(*row))    
    def save(self):
        return True
    
    def filter(self, income_ref=None):
        if income_ref == None:
            return []
        r = []
        for t in self.transactions:
            if t.income_reference == income_ref:
                r.append(t)
        return r

if __name__ == '__main__':
    import sys
    
    # r = refresh_rates(default_currency)
    b = Balance(yaml.load(open('i.yml')))
    try:
        e = datetime.strptime(sys.argv[1], "%Y-%m-%d")
    except IndexError:
        e = datetime.now()+timedelta(365,0,0)
    pprint(b._totals(end=e))
    for l in b.incomes:
        l.fix_id()
        # pprint(l.get_sum(datetime.now(), datetime.strptime(sys.argv[1], "%Y-%m-%d")))

    # t = Transactions('t.csv')
    # pprint(t.filter('01addd82-c0b4-49fb-99d7-d972b56e8207'))
    yaml.dump(b.incomes, open('i.yml','w'), explicit_start=True, explicit_end=True)
    # o = list_incomes[0]
    # pprint(o.get_dates())
