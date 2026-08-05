from datetime import datetime


class Transaction:
    """Represents an individual financial transaction (income or expense)."""

    def __init__(self, amount: float, description: str, date: str = None):
        if amount <= 0:
            raise ValueError("Transaction amount must be greater than zero.")

        self.amount = float(amount)
        self.description = description.strip()
        self.date = date if date else datetime.now().strftime("%Y-%m-%d")

    def __repr__(self):
        return f"<Transaction ${self.amount:.2f} - {self.description} ({self.date})>"