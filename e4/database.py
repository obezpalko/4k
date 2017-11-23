#!/usr/bin/env python
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
    Column, DateTime, Date, String, Integer, Enum, Text, ForeignKey, Numeric
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

#  import sqlalchemy.types as types

PRECISSION = decimal.Decimal(10) ** -2

Base = declarative_base()
engine = create_engine('postgresql://e4:og8ozJoch\Olt6@localhost:5432/e4')
session = sessionmaker()
session.configure(bind=engine)

class Users(Base):
    '''
{
  "id": "117702552568097857840",
  "email": "bestia@bondagefriday.com",
  "verified_email": true,
  "name": "Alex Bes (bestia)",
  "given_name": "Alex",
  "family_name": "Bes",
  "link": "https://plus.google.com/117702552568097857840",
  "picture":
    "https://lh5.googleusercontent.com/-NPyNzjEgO9Y/AAAAAAAAAAI/AAAAAAAA1AY/QBodwoLu_7k/photo.jpg",
  "gender": "male",
  "hd": "bondagefriday.com"
}
    '''
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True, name='id')
    email = Column(String, nullable=False)
    name = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    link = Column(String, nullable=True)
    picture = Column(String, nullable=True)


class Interval(Base):
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
    record_id = Column(Integer, primary_key=True, name='id')
    rate_date = Column(DateTime)
    currency_a_id = Column(Integer, ForeignKey('currency.id'))
    currency_b_id = Column(Integer, ForeignKey('currency.id'))
    currency_a = relationship(
        "Currency", primaryjoin='currency.c.id==rates.c.currency_a')
    currency_b = relationship(
        "Currency", primaryjoin='currency.c.id==rates.c.currency_b')
    rate = Column(Numeric(15, 6), nullable=False)

    def __repr__(self):
        return "{}={:.4f}*{}".format(self.currency_b, self.rate, self.currency_a)

    def to_dict(self):
        """convert object to dict/json"""
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
    record_id = Column(Integer, primary_key=True, name='id')
    title = Column(String)
    name = Column(String)
    default = Column(Integer)
    rate = relationship("Rate", foreign_keys=[Rate.currency_b])

    def get_rate(self):
        """return current rate"""
        return DB.query(Rate).filter(Rate.currency_b == self.id).order_by(
            Rate.rate_date.desc()).first()

    def __repr__(self):
        return "{}".format(self.title)

    def to_dict(self):
        """convert object to dict/json"""
        return {
            'id': self.record_id,
            'title': self.title,
            'name': self.name,
            'rate': self.get_rate(),
            'default': self.default
        }


class Income(Base):
    """income and expenditure
    
    all periodic and not income and expenditure
    """
    
    __tablename__ = 'incomes'
    record_id = Column(Integer, primary_key=True, name='id')
    title = Column(String)
    currency_id = Column(Integer, ForeignKey('currency.id'))
    currency = relationship('Currency')
    sum = Column(Numeric(12, 2))
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    period_id = Column(Integer, ForeignKey('intervals.id'))
    period = relationship('Interval')

    def __repr__(self):
        return "{:20s} {}".format(self.title, self.currency)

    def to_dict(self):
        """convert object to dict/json"""
        return {
            'id': self.record_id,
            'title': self.title,
            'currency': self.currency,
            'sum': "{:.2f}".format(self.sum),
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
                'sum': "{:.2f}".format(self.sum),
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
    record_id = Column(Integer, primary_key=True, name='id')
    title = Column(String)
    currency_id = Column(Integer, ForeignKey('currency.id'))
    currency = relationship('Currency')
    transactions = relationship('Transaction', cascade="all, delete-orphan")
    deleted = Column(Enum('y', 'n', name='is_accound_deleted_enum'), default='n')
    show = Column(Enum('y', 'n', name='is_account_shown_enum'), default='y')

    def to_dict(self):
        """convert object to dict/json"""
        return {
            'id': self.record_id,
            'title': self.title,
            'currency': self.currency,
            'sum': "{:.2f}".format(self.sum()),
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


class Transaction(Base):
    """
    """
    __tablename__ = 'transactions'
    record_id = Column(Integer, primary_key=True, name='id')
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
        """convert object to dict/json"""
        return {
            "id": self.record_id,
            "time": self.time.isoformat(),
            "account": self.account,
            "sum": "{:.2f}".format(self.sum),
            "transfer": self.transfer,
            "income": self.income,
            "comment": self.comment
        }

    def __repr__(self):
        return "{:6d} {} {} {} {} {}".format(self.id, self.time, self.account,
                                             self.sum, self.transfer, self.income)


class Payforward(Base):
    """table of regular payments which was payed before described date

    """

    __tablename__ = 'payforwards'
    record_id = Column(Integer, primary_key=True, name='id')
    income_id = Column(Integer, ForeignKey('incomes.id'), nullable=True)
    income = relationship('Income')
    income_date = Column(Date, nullable=False)
    payment_date = Column(Date, nullable=False)
    transaction_id = Column(Integer, ForeignKey(
        'transactions.id'), nullable=False)
    transaction = relationship('Transaction')



Base.metadata.create_all(engine)
DB = session()

if __name__ == '__main__':
    print(DB)
