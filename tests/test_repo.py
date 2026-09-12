# tests/test_repository.py
import pytest
from decimal import Decimal
from datetime import date
from source.persistence.database import engine, Base, init_db
from source.persistence.repositories import BudgetRepository

@pytest.fixture(autouse=True)
def setup_database():
    """Initializes the database before running tests."""
    Base.metadata.drop_all(bind = engine)
    init_db()
    yield
    Base.metadata.drop_all(bind = engine)

def test_add_and_retrieve_category():
    repo = BudgetRepository()
    category = repo.add_category(
        name = "Dining Out",
        category_type = "expense",
    )
    
    assert category.id is not None
    assert category.name == "Dining Out"
    assert category.category_type == "expense"
    assert category.is_archived is False

    alloc = repo.set_monthly_allocation(
        category_id = category.id,
        year = 2026,
        month = 8,
        planned_amount = Decimal("150.00")
    )
    assert alloc.planned_amount == Decimal("150.00")

def test_add_transaction():
    repo = BudgetRepository()
    cat = repo.add_category(
        name = "Utilities",
        category_type= "expense",
    )
    tx = repo.add_transaction(
        amount = Decimal("85.00"),
        trans_date=date.today(),
        category_id= cat.id,
        note = "Electric Bill"
    )

    assert tx.id is not None
    assert tx.amount == Decimal("85.00")
    assert tx.category_id == cat.id

    transactions = repo.get_all_transactions()
    assert len(transactions) == 1
    assert transactions[0].note == "Electric Bill"

def test_archive_category_soft_delete():
    repo = BudgetRepository()
    cat = repo.add_category(name="Gym", category_type="expense")
    
    # Verify soft-delete archiving
    success = repo.delete_category(cat.id)
    assert success is True

    # Active categories should not list archived categories
    active_cats = repo.get_all_categories(include_archived=False)
    assert len(active_cats) == 0

    # Including archived should still return it for historical lookup
    all_cats = repo.get_all_categories(include_archived=True)
    assert len(all_cats) == 1
    assert all_cats[0].is_archived is True