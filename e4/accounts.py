'''
accounts and goals
'''

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import relationship

from sqlalchemy import Column, Integer, ForeignKey, \
    String, Boolean, func, and_
from .base import __base__, DB_SESSION as DB
from .transactions import Transaction


class Account(__base__):
    """
    accounts
    """
    __tablename__ = 'accounts'
    record_id = Column(Integer, primary_key=True, name='id')
    title = Column(String)
    currency_id = Column(Integer, ForeignKey('currency.id'))
    currency = relationship('Currency')
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User')
    transactions = relationship('Transaction', cascade="all, delete-orphan")
    deleted = Column(Boolean, default=False)
    visible = Column(Boolean, default=True)

    @property
    def json(self):  # pylint: disable=C0111
        """convert object to dict/json"""
        return {
            'id': self.record_id,
            'title': self.title,
            'currency': self.currency,
            'balance': "{:.2f}".format(self.balance()),
            'visible': self.visible,
            'deleted': self.deleted
        }

    def fix_balance(self, n_balance, n_date=datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)):   # pylint: disable=C0111
        delta = n_balance - self.balance(n_date)
        if delta == 0:
            return 0
        transaction = Transaction(
            time=n_date, summ=delta,
            account_id=self.record_id, user_id=self.user_id,
            comment='fix account summ'
            )
        DB.add(transaction)
        return transaction.record_id


    def balance(self, end_date=datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)):   # pylint: disable=C0111
        result = DB.query(
            Transaction.account_id,
            func.sum(Transaction.summ).label('total')
        ).filter(
            and_(
                Transaction.account_id == self.record_id,
                Transaction.time <= end_date
            )
        ).group_by(Transaction.account_id).first()
        if result:
            return result[1]
        return Decimal(0.0)


    def __repr__(self):
        return "{:10s}".format(self.title)
