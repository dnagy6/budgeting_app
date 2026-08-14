"""
File: source/domain/transaction.py
Purpose: Defines an individual payment, purchase, or income entry.

What this file does:
- Stores the details for a single financial entry: dollar amount, description, and date.
- Checks to make sure transaction amounts are valid positive numbers.
- Automatically assigns today's date if no date is provided.
"""
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

@dataclass(slots = True)
class Transaction:
    """Represents an individual financial transaction (income or expense)."""

    amount: float
    description: str
    date: Optional[str] = None

    def __post_init__(self):
        if self.amount <= 0:
            raise ValueError("Transaction amount must be greater than zero.")
        self.amount = float(self.amount)
        self.description = self.description.strip()
        if not self.date:
            self.date = datetime.now().strftime("%Y-%m-%d")