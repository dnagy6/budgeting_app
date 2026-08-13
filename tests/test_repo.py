# tests/test_repository.py
import pytest
from decimal import Decimal
from datetime import date
from source.persistence.database import engine, Base, init_db
from source.persistence.repository import BudgetRepository

@pytest.fixture(autouse=True)
def setup_database():
    """Initializes the database before running tests."""
    Base.metadata.drop_all(bind = engine)
    init_db()
    yield
    Base.metadata.drop_all(bind = engine)

def test_add_and_retrieve_category():
    repo = BudgetRepository()
    category = repo.add_category("Dining Out", Decimal("150.00"))
    
    assert category.id is not None
    assert category.name == "Dining Out"
    assert category.allocated_amount == Decimal("150.00")

def test_add_transaction():
    repo = BudgetRepository()
    cat = repo.add_category("Utilities", Decimal("200.00"))
    tx = repo.add_transaction(Decimal("85.00"), date.today(), category_id=cat.id)

    assert tx.id is not None
    assert tx.amount == Decimal("85.00")
    assert tx.category_id == cat.id