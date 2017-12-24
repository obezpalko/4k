'''
payforward object
'''

from sqlalchemy.orm import relationship
from sqlalchemy import Column, Date, Integer, ForeignKey
from .base import __base__

class Payforward(__base__):  # pylint: disable=R0903
    """table of regular payments which was payed before described date.
    to manage payments
    also used as indicator of credits

    """

    __tablename__ = 'payforwards'
    record_id = Column(Integer, primary_key=True, name='id')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    income_id = Column(Integer, ForeignKey('incomes.id'), nullable=True)
    income = relationship('Income')
    income_date = Column(Date, nullable=False)
    # payment_date = Column(Date, nullable=False)
    transaction_id = Column(Integer, ForeignKey(
        'transactions.id'), nullable=False)
    transaction = relationship('Transaction')
