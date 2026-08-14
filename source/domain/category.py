"""
File: source/domain/category.py
Purpose: Defines a single budget envelope (like Groceries, Rent, or Paycheck).

What this file does:
- Stores the category name, type (income or expense), and target budget amount.
- Keeps a list of all transactions assigned to this envelope.
- Calculates total actual spending or earnings for this envelope.
- Calculates remaining funds left to spend or pending income expected.
"""
from dataclasses import dataclass, field
from typing import List
from source.domain.transaction import Transaction

@dataclass(slots = True)
class Category:
    """Represents a budget envelope for either Income or Expense."""

    name: str
    category_type: str
    planned_amount: float = 0.0
    transactions: List[Transaction] = field(default_factory=list)

    def __post_init__(self):
        self.name = self.name.strip()
        self.category_type = self.category_type.strip().lower()
        if self.category_type not in ["income", "expense"]:
            raise ValueError("Category type must be either 'income' or 'expense'.")
        self.planned_amount = float(self.planned_amount)

    def add_transaction(self, transaction: Transaction):
        self.transactions.append(transaction)

    def get_actual_amount(self) -> float:
        """Returns total spent (for expenses) or total received (for income)."""
        return sum(t.amount for t in self.transactions)

    def get_remaining_amount(self) -> float:
        """Calculates planned - actual."""
        return self.planned_amount - self.get_actual_amount()