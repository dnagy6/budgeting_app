"""
Purpose: Coordiantes month-to-month budget rollover calculations and transitions without
         inflating monthly or annually recorded income of user.
"""

from typing import Tuple
from source.domain.budget import Budget
from source.services.budget_service import BudgetService

class RolloverService:
    """Manages the logic from closing a month and carrying balances forward."""

    def __init__(self, budget_service: BudgetService):
        self.budget_service = budget_service

    @staticmethod
    def calculate_month_surplus(budget: Budget) -> float:
        """
        Calculates the net unspent cash left at the end of a month.
        Formula: Total Available Funds - Actual Total Spent
        """

        total_available = budget.get_total_available()
        total_actual_spent = sum(
            cat.get_actual_amount()
            for cat in budget.categories
            if cat.category_type == "expense"
        )
        return total_available - total_actual_spent

    @staticmethod
    def get_next_month_year(current_year: int, current_month: int) -> Tuple[int, int]:
        """Calculate next calendar month and year (Dec  -> Jan rollover)"""

        if current_month == 12:
            return current_year + 1, 1
        return current_year, current_month + 1

    def close_and_rollover_month(self, current_budget: Budget) -> Budget:
        """
        Closes out current month, calculates leftover cash pool, loads or creates next month's
        budget, and applies the rollover balance.
        """
        if not self.budget_service:
            raise ValueError("BudgetService is required to load the next month's budget.")
        
        surplus = self.calculate_month_surplus(current_budget)
        next_year, next_month = self.get_next_month_year(
            current_budget.year, current_budget.month
        )

        next_budget = self.budget_service.load_budget(next_year, next_month)
        next_budget.apply_rollover(surplus)

        return next_budget

        