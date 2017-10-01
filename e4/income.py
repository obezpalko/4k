#!/usr/local/bin/python3
"""
income class
"""
from datetime import date, timedelta

try:
    from .utils import next_date
except ImportError:
    from utils import next_date

import decimal
from sqlalchemy import and_, func, create_engine, \
    Column, DateTime, Date, String, Integer, Enum, Text, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import sqlalchemy.types as types

Base = declarative_base()
PRECISSION = decimal.Decimal(10) ** -2


class SqliteNumeric(types.TypeDecorator):
    impl = types.String

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(types.VARCHAR(100))

    def process_bind_param(self, value, dialect):
        return str(value)

    def process_result_value(self, value, dialect):
        return decimal.Decimal(value)

    def python_type(self):
        pass

    def process_literal_param(self, value, dialect):
        pass


Numeric = SqliteNumeric


class Interval(Base):
    """
    define intervals
    """
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
    """
    currenciess and rates
    """
    __tablename__ = 'rates'
    id = Column(Integer, primary_key=True)
    rate_date = Column(DateTime)
    currency_a = Column(Integer, ForeignKey('currency.id'))
    currency_b = Column(Integer, ForeignKey('currency.id'))
    a = relationship(
        "Currency", primaryjoin='currency.c.id==rates.c.currency_a')
    b = relationship(
        "Currency", primaryjoin='currency.c.id==rates.c.currency_b')
    rate = Column(Numeric(12, 2), nullable=False)

    def __repr__(self):
        return "{}={:.4f}*{}".format(self.b, self.rate, self.a)

    def to_dict(self):
        return {
            "id": self.currency_b,
            "title": self.b.title,
            "rate": self.rate,
            "rate_date": self.rate_date.date().isoformat(),
            "default": self.b.default
        }


class Currency(Base):
    """
    currencies definitions
    """
    __tablename__ = 'currency'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    name = Column(String)
    default = Column(Integer)
    rate = relationship("Rate", foreign_keys=[Rate.currency_b])

    def get_rate(self):
        return DB.query(Rate).filter(Rate.currency_b == self.id).order_by(Rate.rate_date.desc()).first()

    def __repr__(self):
        return "{}".format(self.title)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'name': self.name,
            'rate': self.get_rate(),
            'default': self.default
        }


class Income(Base):
    """
    """
    __tablename__ = 'incomes'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    currency_id = Column(Integer, ForeignKey('currency.id'))
    currency = relationship('Currency')  # , back_populates='incomes')
    sum = Column(Numeric(12, 2))
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
            'currency': self.currency,
            'sum': self.sum,
            'start_date': self.start_date.isoformat(),
            'end_date': (None if self.end_date is None else self.end_date.isoformat()),
            'period': self.period
        }

    def get_backlog(self, max_date=date.today().replace(month=(date.today().month + 1))):
        backlog = []

        (last_payment,) = DB.query(func.max(Transaction.time)).filter(
            Transaction.income_id == self.id).first()
        if last_payment is None:
            last_payment = self.start_date
        else:
            last_payment = last_payment + timedelta(1)
        for i in self.get_dates(start_date=last_payment, end_date=max_date):
            backlog.append({
                'id': 0,
                'time': i,
                'origin_time': i,
                'sum': self.sum,
                'income': self,
                'comment': ''
            })
        return backlog

    def get_dates(self,
                  start_date=date.today(),
                  end_date=date.today().replace(year=(date.today().year+1)),
                  ignore_pf=False):
        list_dates = []
        # s = 0
        _start_date = max(start_date, self.start_date)

        if self.end_date:
            # print(self.end_date, _start_date)
            if self.end_date < _start_date:
                return []
            _end_date = min(end_date, self.end_date)
        else:
            _end_date = end_date
        if _start_date > _end_date:
            return []
        if _start_date == self.start_date:
            list_dates.append(_start_date)

        _next_date = next_date(self.start_date, (self.period.value, self.period.item))
        # print(_start_date, _end_date, _next_date)
        while _next_date <= _end_date:
            if _next_date >= _start_date and _next_date <= _end_date:
                #s += int(self.sum)
                list_dates.append(_next_date)
            _next_date = next_date(_next_date, (self.period.value, self.period.item))
        # print(list_dates)
        if ignore_pf:
            return list_dates
        pf_dates = DB.query(Payforward.income_date).filter(
            and_(Payforward.income_id == self.id,
                 and_(Payforward.income_date >= _start_date,
                      Payforward.income_date <= _end_date))).all()
        # print(pf_dates)
        for i, in pf_dates:
            try:
                list_dates.remove(i)
            except ValueError:
                pass
        return list_dates

    def get_sum(
            self,
            start_date=date.today(),
            end_date=date.today().replace(year=(date.today().year + 1)), 
            ignore_pf=False):
        try:
            return len(self.get_dates(start_date, end_date, ignore_pf)) * int(self.sum)
        except IndexError:
            return 0


class Account(Base):
    """
    accounts
    """
    __tablename__ = 'accounts'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    currency_id = Column(Integer, ForeignKey('currency.id'))
    currency = relationship('Currency')
    transactions = relationship('Transaction', cascade="all, delete-orphan")
    deleted = Column(Enum('y', 'n'), default='n')
    show = Column(Enum('y', 'n'), default='y')

    def to_dict(self):
        # decimal.getcontext().prec=PRECISSION
        return {
            'id': self.id,
            'title': self.title,
            'currency': self.currency,
            'sum': self.sum(),
            'show': self.show,
            'deleted': self.deleted
        }

    def sum(self):
        # return func.sum(Transaction.sum)
        # try:
        return decimal.Decimal(DB.query(
            Transaction.account_id,
            func.sum(Transaction.sum).label('total')
        ).filter(
            Transaction.account_id == self.id
        ).group_by(Transaction.account_id).first()[1]).quantize(PRECISSION)
        #except:
        #    return decimal.Decimal(0)

    def __repr__(self):
        return "{:10s}".format(self.title)

'''
class Balance(object):
    def __init__(self, database=None):
        object.__init__(self)
        self.database = database
        self.incomes = []

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
                t["_{}".format(default_currency)] += b * \
                    self.current_rates[i.currency]
        return t
'''

class Transaction(Base):
    """
    """
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    time = Column(Date, nullable=False)
    account_id = Column(Integer, ForeignKey('accounts.id'))
    account = relationship("Account")
    sum = Column(Numeric(12, 2), nullable=False)
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
            "sum": self.sum,
            "transfer": self.transfer,
            "income": self.income,
            "comment": self.comment
        }

    def __repr__(self):
        return "{:6d} {} {} {} {} {}".format(self.id, self.time, self.account,
                                             self.sum, self.transfer, self.income)


class Payforward(Base):
    """
    """
    __tablename__ = 'payforwards'
    id = Column(Integer, primary_key=True)
    income_id = Column(Integer, ForeignKey('incomes.id'), nullable=True)
    income = relationship("Income")  # , back_populates='transactions')
    income_date = Column(Date, nullable=False)
    payment_date = Column(Date, nullable=False)
    transaction_id = Column(Integer, ForeignKey(
        'transactions.id'), nullable=False)
    transaction = relationship("Transaction")

#
engine = create_engine('sqlite:///e4/e4.db')
session = sessionmaker()

session.configure(bind=engine)
Base.metadata.create_all(engine)

DB = session()


if __name__ == '__main__':
    import sys
    sys.exit()
