from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = "sqlite:///budget.db"

engine = create_engine(DATABASE_URL, echo = False)

SessionLocal = sessionmaker(bind = engine, expire_on_commit = False)

class Base(DeclarativeBase):
    pass

def init_db():
    """Creates tables if they do NOT exist"""
    Base.metadata.create_all(bind = engine)