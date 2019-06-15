"""
  module to define base in one place
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

DB_URL = "postgresql://e4:og8ozJoch\\Olt6@localhost:5432/e4"
OLD_DB_URL = "postgresql://e4:og8ozJoch\\Olt6@localhost:15432/e4"  # use ssh tunnel

__engine__ = create_engine(DB_URL)

#  __old_engine__ = create_engine(OLD_DB_URL)


DB_SESSION = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=__engine__)
)

__base__ = declarative_base()

__base__.query = DB_SESSION.query_property()
