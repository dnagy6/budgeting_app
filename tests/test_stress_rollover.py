from source.domain.budget import Budget
from source.domain.transaction import Transaction
from source.services.rollover_service import RolloverService


def test_scenario_unspent_surplus():
    """Scenario A: Planned $3,000, Actual $3,000, Spent $2,000 -> Should roll over exactly $1,000."""
    august = Budget(month=8, year=2026)
    paycheck, _ = august.add_or_update_category("Paycheck", "income", 3000.0)
    rent, _ = august.add_or_update_category("Rent", "expense", 2000.0)

    # Actuals
    paycheck.add_transaction(Transaction(amount=3000.0, description="Salary"))
    rent.add_transaction(Transaction(amount=2000.0, description="Rent Payment"))

    surplus = RolloverService.calculate_month_surplus(august)
    print(f"\n[Scenario A] Surplus: ${surplus:,.2f} (Expected: $1,000.00)")
    assert surplus == 1000.0


def test_scenario_partial_income_received():
    """Scenario B: Planned $4,000 income, but ONLY received $2,500. Spent $2,000."""
    august = Budget(month=8, year=2026)
    paycheck, _ = august.add_or_update_category("Paycheck", "income", 4000.0)
    rent, _ = august.add_or_update_category("Rent", "expense", 2000.0)

    # Only one paycheck logged ($2,500), second paycheck never came
    paycheck.add_transaction(Transaction(amount=2500.0, description="1st Paycheck"))
    rent.add_transaction(Transaction(amount=2000.0, description="Rent"))

    # What is the actual cash in the bank? ($2,500 - $2,000 = $500)
    # What does our surplus calculate?
    surplus = RolloverService.calculate_month_surplus(august)
    print(f"[Scenario B] Surplus: ${surplus:,.2f} (Real Bank Surplus is $500.00)")
    assert surplus == 500.0


def test_scenario_overspending_deficit():
    """Scenario C: Earned $2,000, but spent $2,400 (Overspent by $400)."""
    august = Budget(month=8, year=2026)
    paycheck, _ = august.add_or_update_category("Paycheck", "income", 2000.0)
    dining, _ = august.add_or_update_category("Dining", "expense", 2000.0)

    paycheck.add_transaction(Transaction(amount=2000.0, description="Salary"))
    dining.add_transaction(Transaction(amount=2400.0, description="Splurge"))

    surplus = RolloverService.calculate_month_surplus(august)
    print(f"[Scenario C] Deficit Rollover: ${surplus:,.2f} (Expected: -$400.00)")
    assert surplus == -400.0