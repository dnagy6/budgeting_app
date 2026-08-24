"""
File: source/domain/category_group.py
Purpose: Aggregate domain entity representing a parent category group.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from source.domain.category import Category


@dataclass(slots=True)
class CategoryGroup:
    name: str
    group_type: str = "expense"  # "income" or "expense"
    categories: List[Category] = field(default_factory=list)
    id: Optional[int] = None
    sort_order: int = 0

    def add_category(self, category: Category):
        """Adds a child envelope to this group if not already present."""
        if category not in self.categories:
            self.categories.append(category)

    def get_category_by_name(self, name: str) -> Optional[Category]:
        """Finds a child category envelope by name."""
        clean = name.strip().lower()
        return next((c for c in self.categories if c.name.lower() == clean), None)

    def get_total_planned(self) -> float:
        """Calculates total planned amount across all child envelopes."""
        return sum(cat.planned_amount for cat in self.categories)

    def get_total_actual(self) -> float:
        """Calculates total spent/received across all child envelopes."""
        return sum(cat.get_actual_amount() for cat in self.categories)
    