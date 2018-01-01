#!/usr/bin/env python

"""
database and tables
"""
import json
from datetime import datetime, timedelta, date
from decimal import Decimal
from sqlalchemy import and_, func, select, \
    Column, Date, String, Integer, Enum, \
    ForeignKey, Numeric, Boolean
from sqlalchemy.orm import relationship
from .utils import next_date
from .transactions import Transaction
from .base import __base__, DB_SESSION, __engine__
from .payforward import Payforward
from .accounts import Account
from .currencies import Currency, Rate


class DBJsonEncoder(json.JSONEncoder):  # pylint: disable=C0111
    def default(self, obj):  # pylint: disable=E0202,W0221
        if isinstance(obj, (Currency, Income, Rate, Interval, Transaction, Account)):
            return obj.json
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return format(obj.__str__())
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


class User(__base__):  # pylint: disable=R0903
    """ user table.

    processing users
    """

    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True, name='id')
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    link = Column(String, nullable=True)
    picture = Column(String, nullable=True)

    def __repr__(self):
        return "{} <{}>".format(self.name, self.email)

    @property
    def json(self):  # pylint: disable=C0111
        return {
            'id':       self.user_id,
            'email':    self.email,
            'name':     self.name,
            'gender':   self.gender,
            'link':     self.link,
            'picture':  self.picture
        }


class Interval(__base__):  # pylint: disable=R0903
    """
    define intervals
    """
    __tablename__ = 'intervals'
    record_id = Column(Integer, primary_key=True, name='id')
    title = Column(String, nullable=False)
    item = Column(Enum('d', 'm', name='intervals_enum'))
    value = Column(Integer, nullable=False)

    def __repr__(self):
        return "{}:{}{}".format(self.title, self.value, self.item)

    @property
    def json(self):  # pylint: disable=C0111
        return {
            'id':       self.record_id,
            'title':    self.title,
            'item':     self.item,
            'value':    self.value
        }




class Income(__base__):
    """income and expenditure

    all periodic and not income and expenditure
    """

    __tablename__ = 'incomes'
    record_id = Column(Integer, primary_key=True, name='id')
    title = Column(String, nullable=False)
    currency_id = Column(Integer, ForeignKey('currency.id'), nullable=False)
    currency = relationship('Currency')
    summ = Column(Numeric(12, 2), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    period_id = Column(Integer, ForeignKey('intervals.id'), nullable=False)
    period = relationship('Interval')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship('User')
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=True)
    account = relationship('Account')
    is_credit = Column(Boolean, default=False)
    deleted = Column(Boolean, default=False)

    def __repr__(self):
        return "{:20s} {}".format(self.title, self.currency)

    @property
    def json(self):  # pylint: disable=C0111
        """convert object to dict/json"""
        return {
            'id':           self.record_id,
            'title':        self.title,
            'currency':     self.currency,
            'summ':         "{:.2f}".format(self.summ),
            'start_date':   self.start_date.isoformat(),
            'end_date':     (None if self.end_date is None else self.end_date.isoformat()),
            'period':       self.period,
            'account':      self.account,
            'is_credit':    self.is_credit
        }

    def get_backlog(self, max_date):
        """[summary]


        Arguments:
            max_date {[type]} -- [description]

        Returns:
            [type] -- [description]
        """

        backlog = []

        (last_payment,) = DB_SESSION.query(func.max(Transaction.time)).filter(
            Transaction.income_id == self.record_id).first()
        if last_payment is None:
            last_payment = self.start_date
        else:
            last_payment = last_payment + timedelta(1)
        for i in self.get_dates(start_date=last_payment, end_date=max_date):
            backlog.append({
                'id': 0,
                'time': i,
                'origin_time': i,
                'summ': "{:.2f}".format(self.summ),
                'income': self,
                'comment': ''
            })
        return backlog

    def get_dates(self, start_date=date.today(), end_date=date.today().replace(year=(date.today().year+1)), ignore_pf=False):   # pylint: disable=C0111,C0301
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
                #s += int(self.summ)
                list_dates.append(_next_date)
            _next_date = next_date(_next_date, (self.period.value, self.period.item))
        # print(list_dates)
        if ignore_pf:
            return list_dates
        pf_dates = DB_SESSION.query(Payforward.income_date).filter(
            and_(Payforward.income_id == self.record_id,
                 and_(Payforward.income_date >= _start_date,
                      Payforward.income_date <= _end_date))).all()
        # print(pf_dates)
        for i, in pf_dates:
            try:
                list_dates.remove(i)
            except ValueError:
                pass
        return list_dates

    def get_summ(self, start_date=date.today(), end_date=date.today().replace(year=(date.today().year + 1)), ignore_pf=False):  # pylint: disable=C0111,C0301
        try:
            return len(self.get_dates(start_date, end_date, ignore_pf)) * int(self.summ)
        except IndexError:
            return 0





__base__.metadata.create_all(__engine__)
#  DB = session()

if __name__ == '__main__':
    SUB_SELECT = select([
        Rate.currency_b_id.label("b_id"),
        func.max(Rate.rate_date).label("rate_date")
    ]).group_by(Rate.currency_b_id).alias('s')

    print(
        DB_SESSION.query(
            Rate.currency_b_id,
            Rate.rate,
            Rate.rate_date
        ).join(SUB_SELECT,
               and_(SUB_SELECT.c.b_id == Rate.currency_b_id, SUB_SELECT.c.rate_date == Rate.rate_date))
        .all()
    )
