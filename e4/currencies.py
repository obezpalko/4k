'''
currencies and rates
'''

import json

from sqlalchemy.orm import relationship


from sqlalchemy import Column, DateTime, Integer, ForeignKey, Numeric, \
    String, CHAR, PrimaryKeyConstraint, Boolean, \
    and_, select, func
from flask import request, session
from .base import __base__, DB_SESSION as DB

class Rate(__base__):  # pylint: disable=R0903
    """
    currenciess and rates
    """
    __tablename__ = 'rates'
    __table_args__ = (
        PrimaryKeyConstraint(
            'rate_date', 'currency_a_id', 'currency_b_id', 'rate'
        ),
    )
    #  record_id = Column(Integer, primary_key=True, name='id')
    rate_date = Column(DateTime)
    currency_a_id = Column(Integer, ForeignKey('currency.id'))
    currency_b_id = Column(Integer, ForeignKey('currency.id'))
    currency_a = relationship(
        "Currency", primaryjoin='currency.c.id==rates.c.currency_a_id')
    currency_b = relationship(
        "Currency", primaryjoin='currency.c.id==rates.c.currency_b_id')
    rate = Column(Numeric(15, 4), nullable=False)

    def __repr__(self):
        return "{}={:.4f}*{}".format(
            self.currency_b, self.rate, self.currency_a
        )
    @property
    def json(self):  # pylint: disable=C0111
        """convert object to dict/json"""
        return {
            "id": self.currency_b_id,
            "title": self.currency_b.title,
            "symbol": self.currency_b.symbol,
            "rate": self.rate,
            "rate_date": self.rate_date.date().isoformat()
        }

class Currency(__base__):
    """
    currencies definitions
    """
    __tablename__ = 'currency'
    record_id = Column(Integer, primary_key=True, name='id')
    title = Column(String)
    name = Column(String)
    symbol = Column(CHAR)
    rate_rel = relationship("Rate", foreign_keys=[Rate.currency_b_id])

    @property
    def rate(self):
        """return current rate"""
        return DB.query(Rate).filter(Rate.currency_b_id == self.record_id).order_by(
            Rate.rate_date.desc()).first()

    def __repr__(self):
        return "{}".format(self.title)

    @property
    def json(self): # pylint: disable=C0111
        """convert object to dict/json"""
        return {
            'id':       self.record_id,
            'title':    self.title,
            'name':     self.name,
            'rate':     self.rate
            }



class UserCurrencies(__base__):  # pylint: disable=R0903
    """ link users to currencies
    """

    __tablename__ = 'user_currencies'
    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'currency_id'),
    )
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User')
    currency_id = Column(Integer, ForeignKey('currency.id'))
    currency = relationship('Currency')
    default = Column(Boolean, default=False, nullable=False)


def currency_get(**kwargs):
    '''
    get list of currency rates
    '''
    max_date_q = select([
        Rate.currency_b_id.label("b_id"),
        func.max(Rate.rate_date).label("rate_date")]).group_by(
            Rate.currency_b_id).alias('max_date_q')
    rates_query = DB.query(
        Rate.currency_b_id, Rate, Rate.rate_date
    ).join(
        max_date_q,
        and_(
            max_date_q.c.b_id == Rate.currency_b_id,
            max_date_q.c.rate_date == Rate.rate_date
        )
    )

    entries = []
    if 'id' in kwargs and kwargs['id']:
        try:
            return rates_query.filter(
                Rate.currency_b_id == kwargs['id']).first()[1].json
        except TypeError:
            return []
    else:
        for rate in rates_query.all():
            entries.append(rate[1].json)
    return entries


def usercurrency_put(**kwargs):
    """ update user currencies

    Arguments:
        **kwargs id -- currency id

    Returns:
        json -- result code
    """

    obj = json.loads(request.data.decode('utf-8', 'strict'))
    updated = 0

    if 'default' in obj and obj['default']:
        # clean previous default
        updated = DB.query(UserCurrencies).filter(
            and_(
                UserCurrencies.user_id == session['user'][0],
                UserCurrencies.currency_id != kwargs['id'])
            ).update(
                {UserCurrencies.default: False},
                synchronize_session='evaluate')
        updated = DB.query(UserCurrencies).filter(
            and_(
                UserCurrencies.user_id == session['user'][0],
                UserCurrencies.currency_id == kwargs['id']
                )
            ).update(
                {UserCurrencies.default: True},
                synchronize_session='evaluate')
        if updated == 0:
            # if not updated nothing - inser new record
            DB.add(UserCurrencies(
                user_id=session['user'][0],
                currency_id=kwargs['id'],
                default=True
                ))
    else:
        DB.add(UserCurrencies(
            user_id=session['user'][0],
            currency_id=kwargs['id']
            ))
    DB.commit()
    return {'result': 'Ok'}


def usercurrency_delete(**kwargs):
    ''' delete user currency '''
    DB.query(UserCurrencies).filter(
        and_(
            UserCurrencies.user_id == session['user'][0],
            UserCurrencies.currency_id == kwargs['id'])
        ).delete(synchronize_session=False)
    DB.commit()
    return {'result': 'Ok'}
