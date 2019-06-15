'''
 manage transactions in separate module
'''
import datetime
import decimal
import json
from sqlalchemy import Column, Date, Integer, Text, ForeignKey, Numeric, \
    desc, asc, and_, or_
from sqlalchemy.orm import relationship
from flask import request, session
from base import __base__, DB_SESSION as DB
from payforward import Payforward
from utils import strip_numbers


class Transaction(__base__):  # pylint: disable=R0903
    """transactions

    list of transactions
    """

    __tablename__ = 'transactions'
    record_id = Column(Integer, primary_key=True, name='id')
    time = Column(Date, nullable=False)
    account_id = Column(Integer, ForeignKey('accounts.id'))
    account = relationship("Account")
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User')
    summ = Column(Numeric(12, 2), nullable=False)
    transfer = Column(Integer, ForeignKey('transactions.id'),
                      nullable=True)  # id of exchange/transfer operation
    income_id = Column(Integer, ForeignKey('incomes.id'), nullable=True)
    income = relationship("Income")  # , back_populates='transactions')
    comments = Column(Text)

    @property
    def json(self):  # pylint: disable=C0111
        """convert object to dict/json"""
        return {
            "id":       self.record_id,
            "time":     self.time.isoformat(),
            "account":  self.account,
            "user":     self.user,
            "summ":     "{:.2f}".format(self.summ),
            "transfer": self.transfer,
            "income":   self.income,
            "comments":  self.comments
        }


    def __repr__(self):
        return "{:6d} {} {} {} {} {} {}".format(self.record_id, self.time, self.account,
                                             self.summ, self.transfer, self.income, self.comments)

def transaction_get(**kwargs): # pylint: disable=C0111
    print(kwargs)
    if kwargs['id'] == 0:
        from .accounts import Account
        from .currencies import Currency
        _limit = int(request.args.getlist('limit')[0]) if request.args.getlist('limit') else 100
        _start = int(request.args.getlist('start')[0]) if request.args.getlist('start') else 0
        _filter = and_(Transaction.user_id == session['user'][0], Transaction.record_id >= _start)
        if request.args.getlist('account'):
            _filter = and_(
                _filter,
                Transaction.account_id.in_(request.args.getlist('account'))
            )
        else:
            if request.args.getlist('currency'):
                _filter = and_(
                    _filter,
                    Currency.title.in_(request.args.getlist('currency'))
                )
        if request.args.getlist('date'):
            _start_date = request.args.getlist('date')[0]
            if _start_date[0] == '=':
                _start_date = _start_date[1:]
                _filter = and_(_filter, Transaction.time == _start_date)
            else:
                _filter = and_(_filter, Transaction.time >= _start_date)
            _end_date = request.args.getlist('date')[-1]
            if _end_date != _start_date:
                _filter = and_(_filter, Transaction.time <= _end_date)
        if request.args.getlist('transfer'):
            _filter = and_(_filter, Transaction.transfer != None)
        _filter_comments = None
        for _match in request.args.getlist('filter'):
            if _filter_comments is None:
                _filter_comments = Transaction.comments.op('~')(_match)
            _filter_comments = or_(_filter_comments, Transaction.comments.op('~*')(_match))
        if _filter_comments is not None:
            _filter = and_(_filter, _filter_comments)
        print(_filter)

        return  DB.query(Transaction).join(Account).join(Currency).filter(
            _filter
            ).order_by(
                asc(Transaction.record_id)
                ).limit(_limit).all()

    return DB.query(Transaction).get(kwargs['id'])

def transaction_delete(**kwargs): # pylint: disable=C0111
    income = DB.query(Transaction).filter_by(record_id=kwargs['id']).delete()
    DB.query(Payforward).filter_by(transaction_id=kwargs['id']).delete()
    DB.commit()
    return {'deleted': income}

def transaction_put(**kwargs): # pylint: disable=C0111,W0613
    obj = json.loads(request.data.decode('utf-8', 'strict'))
    print(obj)
    # try:
    i = Transaction(
        time=datetime.datetime.strptime(obj['time'], '%Y-%m-%d').date(),
        account_id=int(obj['account.id']),
        user_id = session['user'][0],
        summ=decimal.Decimal(strip_numbers(obj['summ'])),
        transfer=int(obj['transfer']) if (obj['transfer'] != '' and int(obj['transfer']) > 0) else None,
        income_id=int(obj['income.id']) if (obj['income.id'] != '' and int(obj['income.id']) > 0) else None,
        comments=obj['comments']
    )
    DB.add(i)
    DB.flush()
    if 'new_account.id' in obj:
        transfer = Transaction(
            time=datetime.datetime.strptime(obj['time'], '%Y-%m-%d').date(),
            account_id=int(obj['new_account.id']),
            user_id = session['user'][0],
            summ=decimal.Decimal(strip_numbers(obj['new_sum'])),
            transfer=int(obj['transfer']) if int(obj['transfer']) > 0 else None,
            income_id=int(obj['income.id']) if int(obj['income.id']) > 0 else None,
            comments=obj['comments']
        )
        DB.add(transfer)
        DB.flush()
        i.transfer = transfer.record_id
        transfer.transfer = i.record_id
    DB.commit()
    # except:
    #    abort(400)
    return i


def transaction_post(**kwargs): # pylint: disable=C0111
    i = DB.query(Transaction).get(kwargs['id'])
    obj = json.loads(request.data.decode('utf-8', 'strict'))
    print(obj)
    print(obj['time'])
    # try:
    i.time = datetime.datetime.strptime(obj['time'], '%Y-%m-%d').date()
    # TODO: check if account valid for this user
    i.account_id = int(obj['account.id']) if obj['account.id'] != '' else None
    i.user_id = session['user'][0]
    i.summ = decimal.Decimal(strip_numbers(obj['summ']))
    # TODO: check if transfer transaction valid for this user
    i.transfer = int(obj['transfer']) if obj['transfer'] not in [
        '0', ''] else None
    i.income_id = int(obj['income.id']) if obj['income.id'] not in [
        '0', ''] else None
    i.comments = obj['comments']
    # except:
    #    abort(400)
    DB.commit()
    return {'updated': DB.query(Transaction).get(kwargs['id']), "previous": i}
