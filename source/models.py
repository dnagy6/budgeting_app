from datetime import date

class Transaction:
    """Represensts a finslge spending, income, or transfer transaction."""

    def __init__(self, id=None, category_id=0, amount=0.0, transaction_date=None, note="", is_transfer=False):
        self.id = id
        self.category_id = category_id
        self.amount = amount
        self.date = transaction_date or date.today()
        self.note = note
        self.is_transfer = is_transfer

class Category:
    """Represents a budget evelope/folder (Income/Expense category) that contains logged transactions."""
    def __init__(self, id=None, budget_id=0, name="", category_type="expense", planned_amount=0.0, transactions=None):
        self.id = id
        self.budget_id = budget_id
        self.name = name
        self.category_type = category_type # 'expense' or 'income'
        self.planned_amount = planned_amount
        self.transactions = transactions if transactions is not None else []

    def get_actual_amount(self):
        """Sums all non-transfer transactions assigned to this category."""
        return sum(t.amount for t in self.transactions if not t.is_transfer)

    def get_remaining_amount(self):
        """Calculates difference between planned budget and actual spent/earned amounts."""
        return self.planned_amount - self.get_actual_amount()


class SavingsAccount:
    """Tracks live total savings balance and manages internal sub-buckets."""

    def __init__(self, id=None, name="", total_balance=0.0, sub_buckets=None):
        self.id = id
        self.name = name
        self.total_balance = total_balance
        self.sub_buckets = sub_buckets if sub_buckets is not None else {}

    def deposit_transfer(self, amount, target_bucket=None):
        """Increases total balance without treating the funds as spent cash."""

        if amount <= 0:
            raise ValueError("Transfer amount must be positive.")
        self.total_balance += amount
        if target_bucket:
            self.sub_buckets[target_bucket] = self.sub_buckets.get(target_bucket, 0.0) + amount

    def withdraw_transfer(self, amount, source_bucket=None):
        """Decreases total balance for withdrawals or transfers back to checking."""

        if amount > self.total_balance:
            raise ValueError("Insufficient savings balance.")
        self.total_balance -= amount
        if source_bucket and source_bucket in self.sub_buckets:
            self.sub_buckets[source_bucket] = max(0.0, self.sub_buckets[source_bucket] - amount)

class Budget:
    """Represents a full monthly budget containing income and expense categories."""

    def __init__(self, id=None, month=None, year=None, categories=None):
        self.id = id
        self.month = month
        self.year = year
        self.categories = categories if categories is not None else []

    def get_total_income(self):
        """Sums all planned income amounts across income categories."""
        return sum(c.planned_amount for c in self.categories if c.category_type == "income")

    def get_total_allocated(self):
        """Sums all planned expense allocations."""
        return sum(c.planned_amount for c in self.categories if c.category_type == "expense")

    def get_remaining_to_budget(self):
        """Calculates zero-based unassigned balance (Income - Allocated)."""
        return self.get_total_income() - self.get_total_allocated()

    def apply_rollover(self, amount, target_category_name):
        """Applies leftover unbudgeted cash from a previous month as new income."""
        if amount <= 0:
            return

        for category in self.categories:
            if category.name.lower() == target_category_name.lower():
                category.planned_amount += amount
                return

        new_category = Category(
            id=None,
            budget_id=self.id or 0,
            name = target_category_name,
            category_type = "expense",
            planned_amount = amount
        )
        self.categories.append(new_category)
