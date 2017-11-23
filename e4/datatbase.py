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
    Column, DateTime, Date, String, Integer, Enum, Text, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import sqlalchemy.types as types

PRECISSION = decimal.Decimal(10) ** -2

Base = declarative_base()
engine = create_engine('postgresql://e4:og8ozJoch\Olt6@ip6-localhost:5432/e4')
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
  "picture": "https://lh5.googleusercontent.com/-NPyNzjEgO9Y/AAAAAAAAAAI/AAAAAAAA1AY/QBodwoLu_7k/photo.jpg",
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
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship("Users")
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

Base.metadata.create_all(engine)
DB = session()

if __name__ == '__main__':
    print(DB)
