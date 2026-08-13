from decimal import Decimal
from datetime import date
from typing import List, Optional
from sqlalchemy import select
from source.persistence.database import SessionLocal
from source.persistence.models import CategoryModel, TransactionModel


class BudgetRepository:
    """Handles database CRUD operations for categories and transactions."""

    # CATEGORY OPERATIONS

    def add_category(self, name: str, allocated_amount: Decimal = Decimal("0.00")) -> CategoryModel:
        """Creates and saves a new category."""
        with SessionLocal() as session:
            category = CategoryModel(
                name=name,
                allocated_amount=allocated_amount
            )
            session.add(category)
            session.commit()
            session.refresh(category)
            return category

    def get_all_categories(self) -> List[CategoryModel]:
        """Retrieves all categories ordered alphabetically by name."""
        with SessionLocal() as session:
            stmt = select(CategoryModel).order_by(CategoryModel.name)
            return list(session.scalars(stmt).all())

    def get_category_by_id(self, category_id: int) -> Optional[CategoryModel]:
        """Fetches a single category by its primary key ID."""
        with SessionLocal() as session:
            return session.get(CategoryModel, category_id)

    def delete_category(self, category_id: int) -> bool:
        """Deletes a category by ID. Returns True if deleted."""
        with SessionLocal() as session:
            category = session.get(CategoryModel, category_id)
            if category:
                session.delete(category)
                session.commit()
                return True
            return False

    # TRANSACTION OPERATIONS

    def add_transaction(
        self, 
        amount: Decimal, 
        trans_date: date, 
        category_id: Optional[int] = None, 
        note: Optional[str] = None
    ) -> TransactionModel:
        """Creates and saves a new transaction."""
        with SessionLocal() as session:
            transaction = TransactionModel(
                amount=amount,
                trans_date=trans_date,
                category_id=category_id,
                note=note
            )
            session.add(transaction)
            session.commit()
            session.refresh(transaction)
            return transaction

    def get_all_transactions(self) -> List[TransactionModel]:
        """Retrieves all transactions sorted with newest dates first."""
        with SessionLocal() as session:
            stmt = select(TransactionModel).order_by(TransactionModel.trans_date.desc())
            return list(session.scalars(stmt).all())

    def delete_transaction(self, transaction_id: int) -> bool:
        """Deletes a transaction by ID. Returns True if deleted."""
        with SessionLocal() as session:
            transaction = session.get(TransactionModel, transaction_id)
            if transaction:
                session.delete(transaction)
                session.commit()
                return True
            return False