#!/usr/local/bin/python3
"""
Processing currencies
"""
import sqlite3
from sqlite3 import dbapi2 as sqlite
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, \
  Boolean, DateTime, Float, PrimaryKeyConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
import datetime

Base = declarative_base()

class Currency(Base):
  __tablename__ = 'currency'
  __table_args__ = (
        UniqueConstraint('name'),
  )
  id = Column(Integer, primary_key=True)
  name = Column(String)
  default = Column(Boolean, default=False)
  
class CurrencyRates(Base):
  __tablename__ = 'rates'
  __table_args__ = (
        PrimaryKeyConstraint('date', 'a', 'b', 'rate'),
  )

  date = Column(DateTime)
  a = Column(Integer, ForeignKey('currency.id'))
  #a = relationship('Currency', backref=backref('rates', uselist=True))
  b = Column(Integer, ForeignKey('currency.id'))
  #b = relationship('Currency', backref=backref('rates', uselist=True))
  
  rate = Column(Float, default=1.0)


if __name__ == '__main__':
  from sqlalchemy import create_engine
  engine = create_engine('sqlite+pysqlite:///test.db',
    module=sqlite,
    connect_args={'detect_types': sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES},
    native_datetime=True)
  
  from sqlalchemy.orm import sessionmaker
  session = sessionmaker()
  session.configure(bind=engine)
  Base.metadata.create_all(engine)

  c = Currency(name='ILS', default=True)
  s = session()
  s.add(c)
  s.add(Currency(name='USD', default=0))
  s.add(CurrencyRates(date=datetime.datetime.now(), a=1, b=3, rate=3.0))
  s.commit()