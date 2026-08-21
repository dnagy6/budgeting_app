from decimal import Decimal
from datetime import datetime, date
from typing import Optional

from source.domain.budget import Budget
from source.domain.category import Category
from source.domain.transaction import Transaction
from source.persistence.repository import BudgetRepository


class BudgetService:
    """Coordinates domain model logic and database persistence."""

    def __init__(self, repository: BudgetRepository):
        self.repository = repository

    def load_budget(self, year: int, month: int) -> Budget:
        """Loads categories, monthly allocations, and transactions into a Budget domain instance."""
        budget = Budget(month=month, year=year)
        
        # 1. Fetch all category definitions (including archived) and allocations for this month
        all_categories = self.repository.get_all_categories(include_archived=True)
        cat_lookup = {c.id: c for c in all_categories}

        monthly_allocations = self.repository.get_allocations_for_month(year, month)
        alloc_map = {alloc.category_id: float(alloc.planned_amount) for alloc in monthly_allocations}

        # 2. Attach transactions
        db_transactions = self.repository.get_all_transactions()
        month_transactions = [
            tx for tx in db_transactions
            if tx.trans_date and tx.trans_date.year == year and tx.trans_date.month == month
        ]

        # 3. Only include categories that have an allocation OR transactions this month
        active_cat_ids = set(alloc_map.keys()) | {tx.category_id for tx in month_transactions if tx.category_id}

        for cat_id in active_cat_ids:
            db_cat = cat_lookup.get(cat_id)
            if db_cat:
                planned = alloc_map.get(cat_id, 0.0)
                budget.add_or_update_category(
                    name=db_cat.name,
                    category_type=db_cat.category_type,
                    planned_amount=planned
                )

        # 4. Attach transactions to their envelopes
        for db_tx in month_transactions:
            db_cat = cat_lookup.get(db_tx.category_id)
            if db_cat:
                cat = budget.get_category_by_name(db_cat.name)
                if cat:
                    tx_date = db_tx.trans_date.strftime("%Y-%m-%d") if db_tx.trans_date else None
                    cat.add_transaction(
                        Transaction(
                            amount=float(db_tx.amount),
                            description=db_tx.note or "",
                            date=tx_date
                        )
                    )

        return budget
    
    def save_category(
        self, 
        budget: Budget, 
        name: str, 
        category_type: str, 
        planned_amount: float, 
        old_name: Optional[str] = None
    ) -> Category:
        """Saves category definition and stores the montly allocation for this SPECIFIC month."""
        # 1. Update SQLite
        if old_name:
            self.repository.update_category_name(
                old_name=old_name,
                new_name=name,
                category_type=category_type,
            )
            # Find category to fetch its ID
            categories = self.repository.get_all_categories(include_archived=True)
            db_cat = next((c for c in categories if c.name.lower() == name.lower()), None)
        else:
            db_cat = self.repository.add_category(
                name=name,
                category_type=category_type,
            )
        # 2. Save month-specific allocation
        if db_cat:
            self.repository.set_monthly_allocation(
                category_id=db_cat.id,
                year=budget.year,
                month=budget.month,
                planned_amount=Decimal(str(planned_amount))
            )

        # 3. Update In-Memory Domain Model
        category, _ = budget.add_or_update_category(
            name=name,
            category_type=category_type,
            planned_amount=planned_amount
        )
        return category

    def delete_category(self, budget: Budget, name: str) -> bool:
        """Removes category from this specific month's budget without affecting other months."""
        categories = self.repository.get_all_categories(include_archived=True)
        db_cat = next((c for c in categories if c.name.lower() == name.lower()), None)

        if db_cat:
            # Delete only this month's allocation record
            self.repository.delete_monthly_allocation(db_cat.id, budget.year, budget.month)

        # Remove from in-memory domain budget
        cat = budget.get_category_by_name(name)
        if cat and cat in budget.categories:
            budget.categories.remove(cat)
            return True
        return False
    
    def copy_previous_month_budget(
            self,
            target_year: int,
            target_month: int
        ) -> bool:
        """Copies planned amounts from the previous calendar month into the target month."""
        if target_month == 1:
            prev_year, prev_month = target_year - 1, 12
        else:
            prev_year, prev_month = target_year, target_month - 1

        return self.repository.copy_month_allocations(
            from_year=prev_year,
            from_month=prev_month,
            to_year=target_year,
            to_month=target_month
        )

    def has_budget_for_month(self, year: int, month: int) -> bool:
        """Checks if any allocations exist for the given month."""
        allocs = self.repository.get_allocations_for_month(year, month)
        return len(allocs) > 0

    def initialize_fresh_month(self, year: int, month: int):
        """Initializes a new month with all active categories set to $0.00."""
        categories = self.repository.get_all_categories(include_archived=False)
        for cat in categories:
            self.repository.set_monthly_allocation(cat.id, year, month, Decimal("0.00"))

    def zero_out_month(self, year: int, month: int):
        """Sets all planned amounts in the current month to $0.00."""
        self.repository.zero_out_month_allocations(year, month)
        
    def log_transaction(
        self, 
        budget: Budget, 
        category_name: str, 
        amount: float, 
        description: str, 
        date_str: Optional[str] = None
    ) -> Optional[Transaction]:
        """Saves transaction to SQLite and assigns it to the target category envelope."""
        cat = budget.get_category_by_name(category_name)
        if not cat:
            return None

        # Parse date
        try:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else date.today()
        except ValueError:
            parsed_date = date.today()

        # Find category ID in DB
        category_id = None
        for db_cat in self.repository.get_all_categories(include_archived=True):
            if db_cat.name.lower() == category_name.lower():
                category_id = db_cat.id
                break

        # 1. Persist to DB
        self.repository.add_transaction(
            amount=Decimal(str(amount)),
            trans_date=parsed_date,
            category_id=category_id,
            note=description
        )

        # 2. Add to in-memory domain object
        tx = Transaction(amount=amount, description=description, date=date_str)
        cat.add_transaction(tx)
        return tx