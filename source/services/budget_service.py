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
        """Loads categories and transactions from the database into a Budget domain instance."""
        budget = Budget(month=month, year=year)
        
        # 1. Populate categories from DB
        db_categories = self.repository.get_all_categories()
        category_id_map = {}

        for db_cat in db_categories:
            category_id_map[db_cat.id] = db_cat.name
            budget.add_or_update_category(
                name=db_cat.name,
                category_type=db_cat.category_type,
                planned_amount=float(db_cat.allocated_amount)
            )

        # 2. Attach transactions
        db_transactions = self.repository.get_all_transactions()
        for db_tx in db_transactions:
            # DATE FILTER
            if db_tx.trans_date:
                if db_tx.trans_date.year != year or db_tx.trans_date.month != month:
                    continue
                
            cat_name = category_id_map.get(db_tx.category_id)
            if cat_name:
                cat = budget.get_category_by_name(cat_name)
                if cat:
                    tx_date = db_tx.trans_date.strftime("%Y-%m-%d") if db_tx.trans_date else None
                    tx = Transaction(
                        amount=float(db_tx.amount),
                        description=db_tx.note or "",
                        date=tx_date
                    )
                    cat.add_transaction(tx)

        return budget

    def save_category(
        self, 
        budget: Budget, 
        name: str, 
        category_type: str, 
        planned_amount: float, 
        old_name: Optional[str] = None
    ) -> Category:
        """Saves category to the database and updates the in-memory budget."""
        # 1. Update SQLite
        if old_name:
            self.repository.update_category_by_name(
                old_name=old_name,
                new_name=name,
                category_type=category_type,
                allocated_amount=Decimal(str(planned_amount))
            )
        else:
            self.repository.add_category(
                name=name,
                category_type=category_type,
                allocated_amount=Decimal(str(planned_amount))
            )

        # 2. Update In-Memory Domain Model
        category, _ = budget.add_or_update_category(
            name=name,
            category_type=category_type,
            planned_amount=planned_amount
        )
        return category

    def delete_category(self, budget: Budget, name: str) -> bool:
        """Removes category from SQLite and the in-memory budget."""
        # 1. Delete from DB
        deleted = self.repository.delete_category_by_name(name)
        
        # 2. Delete from in-memory domain
        cat = budget.get_category_by_name(name)
        if cat and cat in budget.categories:
            budget.categories.remove(cat)
            
        return deleted

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
        for db_cat in self.repository.get_all_categories():
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