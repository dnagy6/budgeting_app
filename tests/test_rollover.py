from source.domain.budget import Budget
from source.domain.transaction import Transaction
from source.services.rollover_service import RolloverService

def test_rollover_surplus_calculation():
    budget = Budget(month=8, year=2026)
    budget.add_or_update_category("Paycheck", "income", 3000.0)
    rent, _ = budget.add_or_update_category("Rent", "expense", 1200.0)
    groceries, _ = budget.add_or_update_category("Groceries", "expense", 500.0)

    # Actual spending
    rent.add_transaction(Transaction(1200.0, "August Rent"))
    groceries.add_transaction(Transaction(350.0, "Trader Joe's"))

    # Earned $3000, Spent $1550 -> Remaining Surplus = $1450
    surplus = RolloverService.calculate_month_surplus(budget)
    assert surplus == 1450.0


def test_rollover_with_starting_pool():
    """Verify surplus includes existing rollover pool."""
    budget = Budget(month=8, year=2026, rollover_amount=200.0)
    budget.add_or_update_category("Paycheck", "income", 1000.0)
    dining, _ = budget.add_or_update_category("Dining Out", "expense", 300.0)

    dining.add_transaction(Transaction(amount=150.0, description="Dinner"))

    # Total Available ($1000 + $200) - Spent $150 = $1050
    surplus = RolloverService.calculate_month_surplus(budget)
    assert surplus == 1050.0


def test_date_transition_standard_and_year_end():
    """Verify month increments correctly, including December to January."""
    next_year, next_month = RolloverService.get_next_month_year(2026, 8)
    assert next_year == 2026
    assert next_month == 9

    dec_year, dec_month = RolloverService.get_next_month_year(2026, 12)
    assert dec_year == 2027
    assert dec_month == 1