"""
File: source/domain/budget.py
Purpose: Manages a full monthly budget.

What this file does:
- Holds all category envelopes for a specific month and year.
- Adds new categories or updates existing ones.
- Calculates total planned income versus total planned expenses.
- Figures out how much money is left to assign ("Left to Budget").
"""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from source.domain.category import Category

@dataclass(slots = True)
class Budget:
    """Container for managing a monthly zero-based budget."""

    month: int
    year: int
    categories: List[Category] = field(default_factory=list)
    rollover_amount: float = 0.0

    def apply_rollover(self, amount:float):
        """Applies starting rollover balance to this month's pool"""
        self.rollover_amount += float(amount)

    def get_category_by_name(self, name: str) -> Optional[Category]:
        """Finds an existing category envelope by name (case-insensitive)."""
        clean_name = name.strip().lower()
        return next((cat for cat in self.categories if cat.name.lower() == clean_name), None)

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
        """Pure EARNED income for this month only (avoids reporting inflation)"""
        return sum(cat.planned_amount for cat in self.categories if cat.category_type.lower() == "income")

    def get_total_allocated(self) -> float:
        """total planned expense allocation"""
        return sum(cat.planned_amount for cat in self.categories if cat.category_type.lower() == "expense")

    def get_total_available(self) -> float:
        """Total assignable cash pool: Earned income + rollover balance."""
        return self.get_total_income() + self.rollover_amount

    def get_remaining_to_budget(self) -> float:
        """Left to Budget = Total Income - Total Expense Allocations."""
        return self.get_total_available() - self.get_total_allocated()