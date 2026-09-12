"""
File: tests/conftest.py
Purpose: Configures an isolated in-memory SQLite database for all pytest runs.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from source.persistence.database import Base
import source.persistence.database as db_module

@pytest.fixture(scope="function", autouse=True)
def isolated_test_db(monkeypatch):
    """Overrides SessionLocal with an in-memory SQLite database for each test run."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    # Create all tables in memory
    Base.metadata.create_all(bind=test_engine)

    # Monkeypatch the production SessionLocal so repositories write only to memory
    monkeypatch.setattr(db_module, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(db_module, "engine", test_engine)

    yield

    # Teardown in-memory tables
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()