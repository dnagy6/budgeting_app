from decimal import Decimal
from datetime import datetime, date
from typing import Optional

from source.domain.budget import Budget
from source.domain.category import Category
from source.domain.transaction import Transaction
from source.persistence.repository import BudgetRepository

from source.persistence.models import MonthlyGroupStateModel


class BudgetService:
    """Coordinates domain model logic and database persistence."""

    def __init__(self, repository: BudgetRepository):
        self.repository = repository

    def load_budget(self, year: int, month: int) -> Budget:
        """Loads groups, categories, monthly allocations, and tracked transactions into Budget."""
        budget = Budget(month=month, year=year)

        db_groups = self.repository.get_all_category_groups()
        group_lookup = {g.id: g for g in db_groups}

        # 1. Ensure a global "Income" group exists and is strictly typed as "income"
        income_db_grp = next((g for g in db_groups if g.group_type == "income" or g.name.lower() == "income"), None)
        if not income_db_grp:
            income_db_grp = self.repository.add_category_group(
                name="Income",
                group_type="income",
                sort_order=-999
            )
            db_groups = self.repository.get_all_category_groups()
            group_lookup = {g.id: g for g in db_groups}
        elif income_db_grp.group_type != "income":
            # Force correct type if it was previously created as an expense
            income_db_grp.group_type = "income"

        # 2. Force the Income group to be active for this specific month
        if not self.repository.has_monthly_state(income_db_grp.id, year, month):
            self.repository.set_group_active_state(income_db_grp.id, year, month, is_active=True)

        all_categories = self.repository.get_all_categories(include_archived=True)
        cat_lookup = {c.id: c for c in all_categories}

        # 3. Fetch allocations and tracked transactions for this month
        monthly_allocations = self.repository.get_allocations_for_month(year, month)
        alloc_map = {alloc.category_id: float(alloc.planned_amount) for alloc in monthly_allocations}

        db_transactions = self.repository.get_all_transactions(status="tracked")
        month_transactions = [
            tx for tx in db_transactions
            if tx.trans_date and tx.trans_date.year == year and tx.trans_date.month == month
        ]

        active_cat_ids = set(alloc_map.keys()) | {tx.category_id for tx in month_transactions if tx.category_id}
        active_group_ids = {
            cat_lookup[cat_id].group_id
            for cat_id in active_cat_ids
            if cat_id in cat_lookup and cat_lookup[cat_id].group_id in group_lookup
        }

        # 4. Instantiate groups: ensure existing groups are active for this month by default
        for db_grp in db_groups:
            is_active = self.repository.is_group_active_for_month(db_grp.id, year, month)
            if not self.repository.has_monthly_state(db_grp.id, year, month):
                self.repository.set_group_active_state(db_grp.id, year, month, is_active=True)
                is_active = True

            has_active_cats = db_grp.id in active_group_ids
            is_income = db_grp.group_type == "income" or db_grp.name.lower() == "income"

            if has_active_cats or is_active or is_income:
                budget.get_or_create_group(name=db_grp.name, group_type="income" if is_income else db_grp.group_type)

        # 5. Attach active categories and their parent groups
        for cat_id in active_cat_ids:
            db_cat = cat_lookup.get(cat_id)
            if db_cat:
                planned = alloc_map.get(cat_id, 0.0)
                grp_name = group_lookup[db_cat.group_id].name if db_cat.group_id in group_lookup else None
                if grp_name:
                    budget.add_or_update_category(
                        name=db_cat.name,
                        category_type=db_cat.category_type,
                        planned_amount=planned,
                        group_name=grp_name
                    )

        # 6. Sort groups: Income ALWAYS at index 0, followed by user custom order
        user_groups = [g for g in budget.groups if g.group_type != "income" and g.name.lower() != "income"]
        group_order_map = {g.name.lower(): idx for idx, g in enumerate(db_groups)}
        user_groups.sort(key=lambda g: group_order_map.get(g.name.lower(), 999))
        
        income_groups = [g for g in budget.groups if g.group_type == "income" or g.name.lower() == "income"]
        budget.groups = income_groups + user_groups

        # 7. Attach transactions to envelopes
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
            # Pass budget year and month so the group state stays active for this month
            grp = self.repository.add_category_group(
                name=group_name,
                group_type=category_type,
                year=budget.year,
                month=budget.month
            )
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
        Deletes a category group strictly for the current month by clearing child 
        allocations and marking the group inactive for this month only.
        """
        clean_name = group_name.strip().lower()
        target_group = next((g for g in budget.groups if g.name.lower() == clean_name), None)

        if target_group:
            all_cats = self.repository.get_all_categories(include_archived=True)
            name_to_id = {c.name.lower(): c.id for c in all_cats}

            # 1. Clear monthly allocations for this month only
            for cat in target_group.categories:
                cat_id = name_to_id.get(cat.name.lower())
                if cat_id:
                    self.repository.delete_monthly_allocation(
                        category_id=cat_id,
                        year=budget.year,
                        month=budget.month
                    )

            # 2. Mark group inactive for this specific month
            db_groups = self.repository.get_all_category_groups()
            db_grp = next((g for g in db_groups if g.name.lower() == clean_name), None)
            if db_grp:
                self.repository.set_group_month_active(db_grp.id, budget.year, budget.month, is_active=False)

            # 3. Remove from active domain model view
            budget.groups.remove(target_group)
            for cat in list(target_group.categories):
                if cat in budget.categories:
                    budget.categories.remove(cat)

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