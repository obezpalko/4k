#!/usr/local/bin/python3
"""
income class
"""
from datetime import datetime, date, time, timedelta
try:
    from .utils import *
except ModuleNotFoundError:
    from utils import *
from json import JSONEncoder
from sqlalchemy import Column, DateTime, Date, String, Integer, Enum, Float, Text, ForeignKey, create_engine, func
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy.ext.declarative import declarative_base


default_currency = 'ILS'
Base = declarative_base()

class Interval(Base):
    __tablename__ = 'intervals'
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    item = Column(Enum('d', 'm'))
    value = Column(Integer, nullable=False)

    def __repr__(self):
        return "{}:{}{}".format(self.title, self.value, self.item)
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "item": self.item,
            "value": self.value
        }

class Rate(Base):
    __tablename__ = 'rates'
    id = Column(Integer, primary_key=True)
    rate_date = Column(DateTime)
    currency_a = Column(Integer, ForeignKey('currency.id'))
    currency_b = Column(Integer, ForeignKey('currency.id'))
    a = relationship(
        "Currency", primaryjoin='currency.c.id==rates.c.currency_a')
    b = relationship(
        "Currency", primaryjoin='currency.c.id==rates.c.currency_b')
    rate = Column(Float, nullable=False)

    def __repr__(self):
        return "{}={:.4f}*{}".format(self.b,  self.rate, self.a)

    def to_dict(self):
        return {
            "id": self.currency_b,
            "title": self.b.title,
            "rate": self.rate,
            "rate_date": self.rate_date.date().isoformat(),
            "default": self.b.default
        }

class Currency(Base):
    __tablename__ = 'currency'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    name = Column(String)
    default = Column(Integer)

    def __repr__(self):
        return "{}".format(self.title)

    def to_dict(self):
        return {'id': self.id, 'title': self.title, 'name': self.name, 'default': self.default}


class Income(Base):
    __tablename__ = 'incomes'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    currency_id = Column(Integer, ForeignKey('currency.id'))
    currency = relationship('Currency')  # , back_populates='incomes')
    sum = Column(Float)
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    period_id = Column(Integer, ForeignKey('intervals.id'))
    period = relationship('Interval')  # , back_populates='incomes')


    def __repr__(self):
        return "{:20s} {}".format(self.title, self.currency)
    
    def to_dict(self):
        return {self.id: {
            'id': self.id,
            'title': self.title,
            'currency_id': self.currency_id,
            'currency': self.currency.title,
            'sum': self.sum,    
            'start': self.start_date.isoformat(),
            'end': (None if self.end_date == None else self.end_date.isoformat()),
            'interval': self.period.id,
            'period': self.period.title
        }}
    def get_dates(self, start_date=date.today(), end_date=date.today().replace(year=(date.today().year + 1))):
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
            s = self.sum
            list_dates.append((self.title, _sd, s, self.currency))

        nd = next_date(self.start_date, (self.period.value, self.period.item))
        while nd <= _ed:
            if nd >= _sd and nd <= _ed:
                s += self.sum
                list_dates.append((self.title, nd, s, self.currency))
            nd = next_date(nd, (self.period.value, self.period.item))
        return list_dates

    def get_sum(self, start_date=date.today(), end_date=date.today().replace(year=(date.today().year + 1))):
        try:
            return self.get_dates(start_date, end_date)[-1]
        except IndexError:
            return (self.title, None, 0, self.currency)


class Account(Base):
    __tablename__ = 'accounts'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    currency_id = Column(Integer, ForeignKey('currency.id'))
    currency = relationship('Currency')
    transactions = relationship('Transaction')  # , back_populates='account')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'currency': self.currency
        }
    def __repr__(self):
        return "{:10s}".format(self.title)


class Balance(object):
    def __init__(self, database=None):
        object.__init__(self)
        self.database = database

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
                t["_{}".format(default_currency)] += bal * \
                    self.current_rates[curr]
        return t


class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    time = Column(DateTime, nullable=False)
    account_id = Column(Integer, ForeignKey('accounts.id'))
    account = relationship("Account")  # , back_populates='transactions')
    currency_id = Column(Integer, ForeignKey('currency.id'))
    currency = relationship("Currency")  # , back_populates='transactions')
    sum = Column(Float, nullable=False)
    transfer = Column(Integer, ForeignKey('transactions.id'),
                      nullable=True)  # id of exchange/transfer operation
    income_id = Column(Integer, ForeignKey('incomes.id'), nullable=True)
    income = relationship("Income")  # , back_populates='transactions')
    comment = Column(Text)


    def to_dict(self):
        return {
            "id": self.id,
            "time": self.time,
            "account": self.account,
            "currency": self.currency,
            "sum": self.sum,
            "transfer": self.transfer,
            "income": self.income,
            "comment": self.comment 
        }

    def __repr__(self):
        return "{:6d} {} {} {} {:8.2f} {} {}".format(self.id, self.time, self.account, self.currency, self.sum, self.transfer, self.income)


engine = create_engine('sqlite:///e4/e4.db')
session = sessionmaker()

session.configure(bind=engine)
Base.metadata.create_all(engine)

DB = session()


if __name__ == '__main__':
    import sys

    a1 = Account(title='Cash More', currency_id=1)
    a2 = Account(title='Cash', currency_id=1)
    # s.add(a1)
    # s.add(a2)
    # print(s.query(Account).all())
    a1 = DB.query(Account).get(1)
    a2 = DB.query(Account).get(2)

    # print(a1.id)
    # print(a2.id)
    # s.commit()
    c1 = DB.query(Currency).get(1)
    c2 = DB.query(Currency).filter_by(title='USD').first()
    t1 = Transaction(time=datetime.now(), account=a1, sum=666, currency=c1)
    t2 = Transaction(time=datetime.now(), account=a2, sum=-6666, currency=c2)
    DB.add(t1)
    DB.add(t2)
    # print(s.query(Transaction.id).get(1))
    DB.flush()
    t1.transfer = t2.id
    t2.transfer = t1.id

    #print(t1.id, t2.id)
    # s.commit()

    for t in DB.query(Rate, func.max(Rate.rate_date)).group_by(Rate.currency_b).all():
        print(t, t[0].currency_b)
        

    for t in DB.query(Currency).all():
        print(t)
    for t in DB.query(Income).all():
        print(t.get_dates())
        print(t.to_dict())
    sys.exit()
    for i in DB.query(Income).all():
        print("----")
        # print(i)
        print(i.get_sum())
        #print(i.get_dates(end_date=(datetime.strptime('2018-01-01', '%Y-%m-%d').date())))
    # for i in s.query(Interval).all():
    #    print(i)
    # for i in s.query(Currency).all():
    #    print(i)

    sys.exit()
