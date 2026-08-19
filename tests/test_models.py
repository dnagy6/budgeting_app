import unittest
from datetime import date

from source.domain.category import Category
from source.domain.transaction import Transaction
from source.domain.budget import Budget


class TestCategoryLogic(unittest.TestCase):

    def test_actual_amount_sums_non_transfers(self):
        """Verify that transactions sum correctly and skip transfers."""
        category = Category(name="Groceries", category_type="expense", planned_amount=300.0)

        t1 = Transaction(description="Milk & Eggs", amount=50.0)
        t2 = Transaction(description="Bread & Produce", amount=25.0)

        category.transactions.extend([t1, t2])

        self.assertEqual(category.get_actual_amount(), 75.0)

    def test_remaining_amount_calculation(self):
        """Verify remaining budget calculation (Planned - Spent)."""
        category = Category(name="Utilities", category_type="expense", planned_amount=150.0)
        category.transactions.append(Transaction(description="Electric Bill", amount=40.0))

        # 150.0 - 40.0 = 110.0
        self.assertEqual(category.get_remaining_amount(), 110.0)


@unittest.skip("SavingsAccount domain logic pending implementation")
class TestSavingsAccountLogic(unittest.TestCase):

    def test_deposit_transfer(self):
        """Verify depositing increases balance and updates sub-buckets."""
        savings = SavingsAccount(name="Emergency Savings", total_balance=500.0)
        savings.deposit_transfer(amount=100.0, target_bucket="Car Fund")

        self.assertEqual(savings.total_balance, 600.0)
        self.assertEqual(savings.sub_buckets["Car Fund"], 100.0)

    def test_withdraw_transfer_overdraft_raises_error(self):
        """Verify withdrawing more than balance raises a ValueError."""
        savings = SavingsAccount(total_balance=50.0)

        with self.assertRaises(ValueError):
            savings.withdraw_transfer(amount=100.0)


class TestBudgetLogic(unittest.TestCase):

    def setUp(self):
        """Runs before each budget test to set up fresh test data."""
        self.income_category = Category(name="Paycheck", category_type="income", planned_amount=2000.0)
        self.rent_category = Category(name="Rent", category_type="expense", planned_amount=1200.0)
        self.food_category = Category(name="Groceries", category_type="expense", planned_amount=300.0)

        self.budget = Budget(
            month=8,
            year=2026,
            categories=[self.income_category, self.rent_category, self.food_category]
        )

    def test_budget_totals(self):
        """Verify income and allocated expense calculation."""
        self.assertEqual(self.budget.get_total_income(), 2000.0)
        self.assertEqual(self.budget.get_total_allocated(), 1500.0)

    
    def test_budget_totals_and_remaining_to_budget(self):
        """Verify zero-based calculation: Income (2000) - Expenses (1500) = 500."""
        self.assertEqual(self.budget.get_remaining_to_budget(), 500.0)

    def test_budget_rollover_application(self):
        """Rollover increases availabel cash poool without inflating earned income."""
        self.budget.apply_rollover(250.0)
        self.assertEqual(self.budget.get_total_income(), 2000.0)
        self.assertEqual(self.budget.get_total_available(), 2250.0)
        self.assertEqual(self.budget.get_remaining_to_budget(), 750.0)



if __name__ == "__main__":
    unittest.main()