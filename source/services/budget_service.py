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
        """Loads groups, categories, monthly allocations, and tracked transactions into Budget."""
        budget = Budget(month=month, year=year)

        # 1. Fetch all groups and categories from database
        db_groups = self.repository.get_all_category_groups()
        group_lookup = {g.id: g for g in db_groups}

        all_categories = self.repository.get_all_categories(include_archived=True)
        cat_lookup = {c.id: c for c in all_categories}

        # Count global child categories per group
        group_cats_count = {g.id: 0 for g in db_groups}
        for c in all_categories:
            if c.group_id in group_cats_count:
                group_cats_count[c.group_id] += 1

        # 2. Only pre-instantiate freshly created groups that have 0 categories globally
        for db_grp in db_groups:
            if group_cats_count[db_grp.id] == 0:
                budget.get_or_create_group(name=db_grp.name, group_type=db_grp.group_type)

        # 3. Fetch allocations and tracked transactions for THIS specific month
        monthly_allocations = self.repository.get_allocations_for_month(year, month)
        alloc_map = {alloc.category_id: float(alloc.planned_amount) for alloc in monthly_allocations}

        db_transactions = self.repository.get_all_transactions(status="tracked")
        month_transactions = [
            tx for tx in db_transactions
            if tx.trans_date and tx.trans_date.year == year and tx.trans_date.month == month
        ]

        # 4. Attach active categories and their parent groups to this month's budget
        active_cat_ids = set(alloc_map.keys()) | {tx.category_id for tx in month_transactions if tx.category_id}

        for cat_id in active_cat_ids:
            db_cat = cat_lookup.get(cat_id)
            if db_cat:
                planned = alloc_map.get(cat_id, 0.0)
                grp_name = group_lookup[db_cat.group_id].name if db_cat.group_id in group_lookup else None
                budget.add_or_update_category(
                    name=db_cat.name,
                    category_type=db_cat.category_type,
                    planned_amount=planned,
                    group_name=grp_name
                )

        # 5. Maintain user custom sort order for groups
        group_order_map = {g.name.lower(): idx for idx, g in enumerate(db_groups)}
        budget.groups.sort(key=lambda g: group_order_map.get(g.name.lower(), 999))

        # 6. Attach transactions to envelopes
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
        group_name: Optional[str] = None,
        old_name: Optional[str] = None
    ) -> Category:
        """Saves category definition, sets its parent group, and stores the monthly allocation."""
        group_id = None
        if group_name:
            grp = self.repository.add_category_group(name=group_name, group_type=category_type)
            group_id = grp.id

        # 1. Update or create category in DB
        if old_name:
            self.repository.update_category_name(
                old_name=old_name,
                new_name=name,
                category_type=category_type,
                group_id=group_id
            )
            categories = self.repository.get_all_categories(include_archived=True)
            db_cat = next((c for c in categories if c.name.lower() == name.lower()), None)
        else:
            db_cat = self.repository.add_category(
                name=name,
                category_type=category_type,
                group_id=group_id
            )

        # 2. Save month-specific allocation
        if db_cat:
            self.repository.set_monthly_allocation(
                category_id=db_cat.id,
                year=budget.year,
                month=budget.month,
                planned_amount=Decimal(str(planned_amount))
            )

        # 3. Update in-memory domain budget
        category, _ = budget.add_or_update_category(
            name=name,
            category_type=category_type,
            planned_amount=planned_amount,
            group_name=group_name
        )
        return category

    def move_category_group(self, group_name: str, direction: str) -> bool:
        """Shifts category group order up or down."""
        return self.repository.move_category_group(group_name, direction)

    def reorder_category_groups(self, ordered_names: List[str]) -> bool:
        """Updates the sort order of all category groups."""
        return self.repository.reorder_category_groups(ordered_names)

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

    def delete_category_group(self, budget: Budget, group_name: str) -> bool:
        """
        Deletes a category group for this specific month by deleting monthly allocations
        for all child categories. Cleans up globally only if the group has 0 categories in DB.
        """
        clean_name = group_name.strip().lower()
        target_group = next((g for g in budget.groups if g.name.lower() == clean_name), None)

        if target_group:
            all_cats = self.repository.get_all_categories(include_archived=True)
            name_to_id = {c.name.lower(): c.id for c in all_cats}

            # Delete month allocations only for this month
            for cat in target_group.categories:
                cat_id = name_to_id.get(cat.name.lower())
                if cat_id:
                    self.repository.delete_monthly_allocation(
                        category_id=cat_id,
                        year=budget.year,
                        month=budget.month
                    )

            # Remove from active domain budget
            budget.groups.remove(target_group)
            for cat in list(target_group.categories):
                if cat in budget.categories:
                    budget.categories.remove(cat)

        # If the group has no child categories anywhere in the DB, clean it up
        db_groups = self.repository.get_all_category_groups()
        db_grp = next((g for g in db_groups if g.name.lower() == clean_name), None)
        if db_grp:
            all_db_cats = self.repository.get_all_categories(include_archived=True)
            has_cats = any(c.group_id == db_grp.id for c in all_db_cats)
            if not has_cats:
                self.repository.delete_category_group(db_grp.id)

        return True
    
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

    # ---- TRANSACTIONS ----
        
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

    # TRANSACTION STREAM & STAGING OPERATIONS

    def get_transactions_by_status(
        self,
        year: int,
        month: int,
        status: str = "tracked"
    ) -> list:
        """Fetches transactions matching a specific status and month/year."""
        all_txs = self.repository.get_all_transactions(status=status)
        return [
            tx for tx in all_txs
            if tx.trans_date and tx.trans_date.year == year and tx.trans_date.month == month
        ]

    def get_transaction_status_counts(self, year: int, month: int) -> dict[str, int]:
        """Returns the number of transactions per status tab for a given month."""
        counts = {"new": 0, "tracked": 0, "deleted": 0, "pending": 0}
        all_txs = self.repository.get_all_transactions()
        for tx in all_txs:
            if tx.trans_date and tx.trans_date.year == year and tx.trans_date.month == month:
                if tx.status in counts:
                    counts[tx.status] += 1
        return counts

    def update_transaction_status(self, transaction_id: int, new_status: str) -> bool:
        """Transitions transaction status ('new', 'tracked', 'deleted', 'pending')."""
        return self.repository.update_transaction_status(transaction_id, new_status)

    def hard_delete_transaction(self, transaction_id: int) -> bool:
        """Permanently removes a transaction from SQLite."""
        return self.repository.delete_transaction(transaction_id)