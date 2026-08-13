# test_persistence.py
from decimal import Decimal
from datetime import date
from source.persistence.database import init_db
from source.persistence.repository import BudgetRepository

def run_tests():
    # 1. Initialize Database & Repository
    init_db()
    repo = BudgetRepository()
    print("✅ Database initialized successfully.")

    # 2. Test Category Creation
    print("\n--- Testing Category Creation ---")
    category = repo.add_category(name="Groceries", allocated_amount=Decimal("500.00"))
    print(f"Created Category: ID={category.id}, Name='{category.name}', Allocated=${category.allocated_amount}")

    # 3. Test Transaction Creation linked to Category
    print("\n--- Testing Transaction Creation ---")
    transaction = repo.add_transaction(
        amount=Decimal("75.25"),
        trans_date=date.today(),
        category_id=category.id,
        note="Weekly grocery run"
    )
    print(f"Created Transaction: ID={transaction.id}, Amount=${transaction.amount}, Note='{transaction.note}'")

    # 4. Test Data Retrieval
    print("\n--- Testing Data Retrieval ---")
    all_categories = repo.get_all_categories()
    all_transactions = repo.get_all_transactions()
    
    print(f"Fetched {len(all_categories)} categories: {[c.name for c in all_categories]}")
    print(f"Fetched {len(all_transactions)} transactions: {[(t.amount, t.note) for t in all_transactions]}")

    # 5. Test Unique Constraint Handling (Should raise an exception)
    print("\n--- Testing Unique Name Constraint ---")
    try:
        repo.add_category(name="Groceries")  # Duplicate name
        print("❌ FAIL: Duplicate category allowed!")
    except Exception as e:
        print("✅ SUCCESS: Caught duplicate entry prevention as expected.")

    # 6. Cleanup Test Data
    print("\n--- Testing Deletion ---")
    tx_deleted = repo.delete_transaction(transaction.id)
    cat_deleted = repo.delete_category(category.id)
    print(f"Transaction deleted: {tx_deleted}, Category deleted: {cat_deleted}")

if __name__ == "__main__":
    run_tests()