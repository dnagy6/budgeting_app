from typing import List
from source.domain.transaction import Transaction


class Category:
    """Represents a budget envelope for either Income or Expense."""

    def __init__(self, name: str, category_type: str, planned_amount: float = 0.0):
        category_type_clean = category_type.strip().lower()
        if category_type_clean not in ["income", "expense"]:
            raise ValueError("Category type must be either 'income' or 'expense'.")

        self.name = name.strip()
        self.category_type = category_type_clean
        self.planned_amount = float(planned_amount)
        self.transactions: List[Transaction] = []

    def add_transaction(self, transaction: Transaction):
        self.transactions.append(transaction)

    def get_actual_amount(self) -> float:
        """Returns total spent (for expenses) or total received (for income)."""
        return sum(t.amount for t in self.transactions)

    def get_remaining_amount(self) -> float:
        """
        For Expense: Planned - Actual (Amount left to spend)
        For Income: Planned - Actual (Pending income expected)
        """
        actual = self.get_actual_amount()
        return self.planned_amount - actual

    def __repr__(self):
        return f"<Category '{self.name}' ({self.category_type}) Planned: ${self.planned_amount:.2f}>"