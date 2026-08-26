from decimal import Decimal
from datetime import date
from typing import List, Optional
from sqlalchemy import select
from source.persistence.database import SessionLocal
from source.persistence.models import CategoryGroupModel, CategoryModel, TransactionModel, MonthlyAllocationModel


class BudgetRepository:
    """Handles database CRUD operations for categories and transactions."""

    # CATEGORY GROUP OPERATIONS

    def add_category_group(self, name: str, group_type: str = "expense", sort_order: int = 0) -> CategoryGroupModel:
        """Creates a new category group or returns existing one."""
        with SessionLocal() as session:
            stmt = select(CategoryGroupModel).where(CategoryGroupModel.name == name)
            group = session.scalars(stmt).first()
            if not group:
                group = CategoryGroupModel(name=name, group_type=group_type, sort_order=sort_order)
                session.add(group)
                session.commit()
                session.refresh(group)
            return group

    def get_all_category_groups(self) -> List[CategoryGroupModel]:
        """Retrieves all category groups ordered by sort_order and name."""
        with SessionLocal() as session:
            stmt = select(CategoryGroupModel).order_by(CategoryGroupModel.sort_order, CategoryGroupModel.name)
            return list(session.scalars(stmt).all())

    def delete_category_group(self, group_id: int) -> bool:
        """Deletes a category group and unlinks any child categories."""
        with SessionLocal() as session:
            group = session.get(CategoryGroupModel, group_id)
            if group:
                # Unlink child categories
                stmt = select(CategoryModel).where(CategoryModel.group_id == group_id)
                for cat in session.scalars(stmt).all():
                    cat.group_id = None
                session.delete(group)
                session.commit()
                return True
            return False

    def delete_category_group_by_name(self, name: str) -> bool:
        """Deletes a category group by name and unlinks its child categories."""
        with SessionLocal() as session:
            stmt = select(CategoryGroupModel).where(CategoryGroupModel.name == name.strip())
            group = session.scalars(stmt).first()
            if group:
                # Unlink child categories from this group so they don't get deleted
                stmt_cats = select(CategoryModel).where(CategoryModel.group_id == group.id)
                for cat in session.scalars(stmt_cats).all():
                    cat.group_id = None
                session.delete(group)
                session.commit()
                return True
            return False

    # CATEGORY OPERATIONS

    def add_category(
            self, 
            name: str,
            category_type: str = "expense",
            group_id: Optional[int] = None
        ) -> CategoryModel:
            """Creates a new category or unarchives an existing one and updates group link."""
            with SessionLocal() as session:
                stmt = select(CategoryModel).where(CategoryModel.name == name)
                category = session.scalars(stmt).first()

                if category:
                    category.is_archived = False
                    category.category_type = category_type
                    if group_id is not None:
                        category.group_id = group_id
                else:
                    category = CategoryModel(
                        name=name,
                        category_type=category_type,
                        group_id = group_id,
                        is_archived=False
                    )
                    session.add(category)

                session.commit()
                session.refresh(category)
                return category

    def get_all_categories(self, include_archived: bool = False) -> List[CategoryModel]:
        """Retrieves all categories ordered alphabetically by name."""
        with SessionLocal() as session:
            stmt = select(CategoryModel)
            if not include_archived:
                stmt = stmt.where(CategoryModel.is_archived == False)
            stmt = stmt.order_by(CategoryModel.name)

            return list(session.scalars(stmt).all())

    def get_category_by_id(self, category_id: int) -> Optional[CategoryModel]:
        """Fetches a single category by its primary key ID."""
        with SessionLocal() as session:
            return session.get(CategoryModel, category_id)

    def delete_category(self, category_id: int) -> bool:
        """Soft-deletes a category envelope by archiving it."""
        with SessionLocal() as session:
            category = session.get(CategoryModel, category_id)
            if category:
                category.is_archived = True
                session.commit()
                return True
            return False

    def update_category_name(
        self,
        old_name: str,
        new_name: str,
        category_type: str,
        group_id: Optional[int] = None
    ) -> bool:
        """Updates category name, type, and optional parent group link."""
        with SessionLocal() as session:
            stmt = select(CategoryModel).where(CategoryModel.name == old_name)
            category = session.scalars(stmt).first()
            if category:
                category.name = new_name
                category.category_type = category_type
                if group_id is not None:
                    category.group_id = group_id
                session.commit()
                return True
            return False

    def delete_category_by_name(self, name:str) -> bool:
        """Soft-deletes an envelope by name."""
        with SessionLocal() as session:
            stmt = select(CategoryModel).where(CategoryModel.name == name)
            category = session.scalars(stmt).first()
            if category:
                category.is_archived = True
                session.commit()
                return True
            return False

    def move_category_group(self, group_name: str, direction: str) -> bool:
        """Moves a category group 'up' or 'down' by adjusting sort_order."""
        with SessionLocal() as session:
            stmt = select(CategoryGroupModel).order_by(CategoryGroupModel.sort_order, CategoryGroupModel.id)
            groups = list(session.scalars(stmt).all())
            
            names = [g.name.lower() for g in groups]
            clean_name = group_name.strip().lower()
            if clean_name not in names:
                return False

            idx = names.index(clean_name)
            if direction == "up" and idx > 0:
                target_idx = idx - 1
            elif direction == "down" and idx < len(groups) - 1:
                target_idx = idx + 1
            else:
                return False

            # Swap sort_order indices and normalize
            groups[idx], groups[target_idx] = groups[target_idx], groups[idx]
            for order, grp in enumerate(groups):
                grp.sort_order = order

            session.commit()
            return True

    def reorder_category_groups(self, ordered_names: List[str]) -> bool:
        """Persists the new display order for category groups."""
        with SessionLocal() as session:
            stmt = select(CategoryGroupModel)
            all_groups = {g.name.lower(): g for g in session.scalars(stmt).all()}
            for order, name in enumerate(ordered_names):
                grp = all_groups.get(name.lower())
                if grp:
                    grp.sort_order = order
            session.commit()
            return True

    def set_monthly_allocation(
            self,
            category_id: int,
            year: int,
            month: int,
            planned_amount: Decimal
    ) -> MonthlyAllocationModel:
        """Sets or updates the planned allocation for a specific category in a specific month."""
        with SessionLocal() as session:
            stmt = select(MonthlyAllocationModel).where(
                MonthlyAllocationModel.category_id == category_id,
                MonthlyAllocationModel.year == year,
                MonthlyAllocationModel.month == month
            )
            allocation = session.scalars(stmt).first()

            if allocation:
                allocation.planned_amount = planned_amount
            else:
                allocation = MonthlyAllocationModel(
                    category_id=category_id,
                    year=year,
                    month=month,
                    planned_amount=planned_amount
                )
                session.add(allocation)

            session.commit()
            session.refresh(allocation)
            return allocation

    def get_allocations_for_month(self, year: int, month: int) -> List[MonthlyAllocationModel]:
        """Retrieves all planned allocations for a given month and year."""
        with SessionLocal() as session:
            stmt = select(MonthlyAllocationModel).where(
                MonthlyAllocationModel.year == year,
                MonthlyAllocationModel.month == month
            )
            return list(session.scalars(stmt).all())

    def copy_month_allocations(
        self,
        from_year: int,
        from_month: int,
        to_year: int,
        to_month: int
    ) -> bool:
        """Copies all planned category amounts from a source month into a target month."""
        with SessionLocal() as session:
            source_allocs = session.scalars(
                select(MonthlyAllocationModel).where(
                    MonthlyAllocationModel.year == from_year,
                    MonthlyAllocationModel.month == from_month
                )
            ).all()

            if not source_allocs:
                return False

            for alloc in source_allocs:
                # Check if target already has an allocation
                existing = session.scalars(
                    select(MonthlyAllocationModel).where(
                        MonthlyAllocationModel.category_id == alloc.category_id,
                        MonthlyAllocationModel.year == to_year,
                        MonthlyAllocationModel.month == to_month
                    )
                ).first()

                if existing:
                    existing.planned_amount = alloc.planned_amount
                else:
                    new_alloc = MonthlyAllocationModel(
                        category_id=alloc.category_id,
                        year=to_year,
                        month=to_month,
                        planned_amount=alloc.planned_amount
                    )
                    session.add(new_alloc)

            session.commit()
            return True

    #-------- TRANSACTION OPERATIONS ----------

    def add_transaction(
        self,
        amount: Decimal,
        trans_date: date,
        category_id: Optional[int] = None,
        note: Optional[str] = None,
        status: str = "tracked",
        external_id: Optional[str] = None
    ) -> TransactionModel:
        """Creates and saves a new transaction."""
        with SessionLocal() as session:
            transaction = TransactionModel(
                amount=amount,
                trans_date=trans_date,
                category_id=category_id,
                note=note,
                status=status,
                external_id=external_id
            )
            session.add(transaction)
            session.commit()
            session.refresh(transaction)
            return transaction

    def get_all_transactions(self, status: Optional[str] = None) -> List[TransactionModel]:
        """Retrieves transactions ordered by date descending, optionally filtered by status."""
        with SessionLocal() as session:
            stmt = select(TransactionModel)
            if status:
                stmt = stmt.where(TransactionModel.status == status)
            stmt = stmt.order_by(TransactionModel.trans_date.desc())
            return list(session.scalars(stmt).all())

    def update_transaction_status(self, transaction_id: int, new_status: str) -> bool:
        """Updates transaction status ('new', 'tracked', 'deleted', 'pending')."""
        with SessionLocal() as session:
            tx = session.get(TransactionModel, transaction_id)
            if tx:
                tx.status = new_status
                session.commit()
                return True
            return False

    def get_transaction_by_external_id(self, external_id: str) -> Optional[TransactionModel]:
        """Fetches a transaction by external/Plaid ID for deduplication."""
        with SessionLocal() as session:
            stmt = select(TransactionModel).where(TransactionModel.external_id == external_id)
            return session.scalars(stmt).first()

    def assign_transaction_category(self, transaction_id: int, category_id: int) -> bool:
        """Assigns an envelope category to a transaction and updates status to tracked."""
        with SessionLocal() as session:
            tx = session.get(TransactionModel, transaction_id)
            if tx:
                tx.category_id = category_id
                tx.status = "tracked"
                session.commit()
                return True
            return False

    def delete_transaction(self, transaction_id: int) -> bool:
        """Permanently deletes a transaction from the database."""
        with SessionLocal() as session:
            tx = session.get(TransactionModel, transaction_id)
            if tx:
                session.delete(tx)
                session.commit()
                return True
            return False

    #------- MONTHLY OPERATIONS -----------

    def delete_monthly_allocation(self, category_id: int, year: int, month: int) -> bool:
        """Deletes only the allocation record for a specific category in a specific month."""
        with SessionLocal() as session:
            stmt = select(MonthlyAllocationModel).where(
                MonthlyAllocationModel.category_id == category_id,
                MonthlyAllocationModel.year == year,
                MonthlyAllocationModel.month == month
            )
            alloc = session.scalars(stmt).first()
            if alloc:
                session.delete(alloc)
                session.commit()
                return True
            return False

    def zero_out_month_allocations(self, year: int, month: int) -> bool:
        """Sets all planned amounts for a specific month to $0.00."""
        with SessionLocal() as session:
            stmt = select(MonthlyAllocationModel).where(
                MonthlyAllocationModel.year == year,
                MonthlyAllocationModel.month == month
            )
            allocations = session.scalars(stmt).all()
            for alloc in allocations:
                alloc.planned_amount = Decimal("0.00")
            session.commit()
            return True

    def get_months_with_allocations(self, year: int) -> List[int]:
        """Returns a list of month numbers (1-12) that have initialized budgets in a given year."""
        with SessionLocal() as session:
            stmt = select(MonthlyAllocationModel.month).where(
                MonthlyAllocationModel.year == year
            ).distinct()
            return list(session.scalars(stmt).all())