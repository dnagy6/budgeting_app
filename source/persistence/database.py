from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = "sqlite:///budget.db"

engine = create_engine(DATABASE_URL, echo = False)

SessionLocal = sessionmaker(bind = engine, expire_on_commit = False)

class Base(DeclarativeBase):
    pass

def init_db():
    """Creates tables if they do NOT exist"""
    Base.metadata.create_all(bind = engine)

    with engine.connect() as conn:
    # Check if 'cursor' column exists on plaid_items
        result = conn.execute(text("PRAGMA table_info(plaid_items)"))
        cols = [row[1] for row in result.fetchall()]
        if "cursor" not in cols and cols:
            conn.execute(text("ALTER TABLE plaid_items ADD COLUMN cursor TEXT"))
            conn.commit()