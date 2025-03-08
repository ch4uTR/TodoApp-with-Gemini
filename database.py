from idlelib.squeezer import Squeezer

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./todoapp.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)
LocalSession = sessionmaker(bind=engine)

Base = declarative_base()