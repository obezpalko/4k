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
from sqlalchemy import Column, VARCHAR, DateTime, Date, String, Integer, Enum, Float, Text, ForeignKey, create_engine, func
from sqlalchemy.orm import relationship, backref, sessionmaker
from sqlalchemy.ext.declarative import declarative_base


default_currency = 'ILS'
Base = declarative_base()
CURRENCY_SCALE=100000
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
    sum = Column(VARCHAR)
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    period_id = Column(Integer, ForeignKey('intervals.id'))
    period = relationship('Interval')  # , back_populates='incomes')


    def __repr__(self):
        return "{:20s} {}".format(self.title, self.currency)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'currency_id': self.currency_id,
            'currency': self.currency.title,
            'sum': float(int(self.sum)/CURRENCY_SCALE),
            'start_date': self.start_date.isoformat(),
            'end_date': (None if self.end_date == None else self.end_date.isoformat()),
            'period_id': self.period.id,
            'period': self.period.title
        }

    def get_backlog(self, max_date=date.today().replace(month=(date.today().month + 1))):
        backlog=[]
        (last_payment,) = DB.query(func.max(Transaction.time)).filter(Transaction.income_id==self.id).first()
        if last_payment == None:
            last_payment = self.start_date
        else:
            last_payment = last_payment + timedelta(1)
        for d in self.get_dates(start_date=last_payment, end_date=max_date):
            backlog.append({
                'id': 0,
                'time': d,
                'sum': int(self.sum)/CURRENCY_SCALE,
                'income': self,
                'comment': ''
                }) #Transaction(time=d, account_id=0, sum=self.sum, income_id=self.id, comment=self.title))
        return backlog

    def get_dates(self, start_date=date.today(), end_date=date.today().replace(year=(date.today().year + 1))):
        list_dates = []
        # s = 0
        _sd = max(start_date, self.start_date)

        if self.end_date:
            _ed = min(end_date, self.end_date)
        else:
            _ed = end_date
        if _sd > _ed:
            return []
        if _sd == self.start_date:
            s = int(self.sum)
            list_dates.append(_sd)

        nd = next_date(self.start_date, (self.period.value, self.period.item))
        while nd <= _ed:
            if nd >= _sd and nd <= _ed:
                #s += int(self.sum)
                list_dates.append(nd)
            nd = next_date(nd, (self.period.value, self.period.item))
        return list_dates

    def get_sum(self, start_date=date.today(), end_date=date.today().replace(year=(date.today().year + 1))):
        try:
            return len(self.get_dates(start_date, end_date))*int(self.sum)
        except IndexError:
            return 0


class Account(Base):
    __tablename__ = 'accounts'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    currency_id = Column(Integer, ForeignKey('currency.id'))
    currency = relationship('Currency')
    transactions = relationship('Transaction')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'currency': self.currency,
            'sum': int(self.sum())/CURRENCY_SCALE
        }

    def sum(self):
        try:
            return DB.query(
                Transaction.account_id,
                func.sum(Transaction.sum).label('total')
                ).filter(
                    Transaction.account_id==self.id
                    ).group_by(Transaction.account_id).first()[1]
        except:
            return "0"

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
            b = i.get_sum(start, end)
            t[curr] += b
            if default_currency == i.currency:
                t["_{}".format(default_currency)] += b
            else:
                t["_{}".format(default_currency)] += b * self.current_rates[i.currency]
        return t


class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    time = Column(Date, nullable=False)
    account_id = Column(Integer, ForeignKey('accounts.id'))
    account = relationship("Account")  # , back_populates='transactions')
    sum = Column(VARCHAR, nullable=False)
    transfer = Column(Integer, ForeignKey('transactions.id'),
                      nullable=True)  # id of exchange/transfer operation
    income_id = Column(Integer, ForeignKey('incomes.id'), nullable=True)
    income = relationship("Income")  # , back_populates='transactions')
    comment = Column(Text)


    def to_dict(self):
        return {
            "id": self.id,
            "time": self.time.isoformat(),
            "account": self.account,
            "sum": float(int(self.sum)/CURRENCY_SCALE),
            "transfer": self.transfer,
            "income": self.income,
            "comment": self.comment 
        }

    def __repr__(self):
        return "{:6d} {} {} {} {} {}".format(self.id, self.time, self.account,  self.sum, self.transfer, self.income)


engine = create_engine('sqlite:///e4/e4.db')
session = sessionmaker()

session.configure(bind=engine)
Base.metadata.create_all(engine)

DB = session()


if __name__ == '__main__':
    sys.exit()
