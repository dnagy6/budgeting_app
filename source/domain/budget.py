from typing import List, Optional, Tuple
from source.domain.category import Category


class Budget:
    """Container for managing a monthly zero-based budget."""

    def __init__(self, month: int, year: int, categories: Optional[List[Category]] = None):
        self.month = month
        self.year = year
        self.categories: List[Category] = categories if categories is not None else []

    def get_category_by_name(self, name: str) -> Optional[Category]:
        for cat in self.categories:
            if cat.name.lower() == name.strip().lower():
                return cat
        return None

    def add_or_update_category(self, name: str, category_type: str, planned_amount: float) -> Tuple[Category, bool]:
        """
        Upserts a category envelope: updates planned amount if it exists,
        or creates a new category if it doesn't.
        Returns (Category, is_new_boolean).
        """
        existing = self.get_category_by_name(name)
        if existing:
            existing.planned_amount = float(planned_amount)
            existing.category_type = category_type.strip().lower()
            return existing, False

        new_cat = Category(name=name, category_type=category_type, planned_amount=planned_amount)
        self.categories.append(new_cat)
        return new_cat, True

    def get_total_income(self) -> float:
        return sum(cat.planned_amount for cat in self.categories if cat.category_type == "income")

    def get_total_allocated(self) -> float:
        return sum(cat.planned_amount for cat in self.categories if cat.category_type == "expense")

    def get_unallocated_amount(self) -> float:
        """Left to Budget = Total Income - Total Expense Allocations."""
        return self.get_total_income() - self.get_total_allocated()

    def __repr__(self):
        return f"<Budget {self.month}/{self.year} Envelopes: {len(self.categories)}>"