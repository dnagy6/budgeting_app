"""
File: source/persistence/repositories/transaction_repository.py
Purpose: Database CRUD operations for actual transactions and cash flow entries.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select

from source.persistence.database import SessionLocal
from source.persistence.models import TransactionModel


class TransactionRepository:
    """Manages persistence for individual ledger transactions, bulk syncing, and status updates."""

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
            tx = TransactionModel(
                amount=amount,
                trans_date=trans_date,
                category_id=category_id,
                note=note,
                status=status,
                external_id=external_id
            )
            session.add(tx)
            session.commit()
            session.refresh(tx)
            return tx

    def get_all_transactions(self, status: Optional[str] = None) -> List[TransactionModel]:
        """Retrieves transactions ordered by date descending, optionally filtered by status."""
        with SessionLocal() as session:
            stmt = select(TransactionModel)
            if status:
                stmt = stmt.where(TransactionModel.status == status)
            stmt = stmt.order_by(TransactionModel.trans_date.desc())
            return list(session.scalars(stmt).all())

    def get_transaction_by_id(self, transaction_id: int) -> Optional[TransactionModel]:
        """Fetches a transaction by its primary key ID."""
        with SessionLocal() as session:
            return session.get(TransactionModel, transaction_id)

    def get_transaction_by_external_id(self, external_id: str) -> Optional[TransactionModel]:
        """Fetches a transaction by external/Plaid ID for deduplication."""
        with SessionLocal() as session:
            stmt = select(TransactionModel).where(TransactionModel.external_id == external_id)
            return session.scalars(stmt).first()

    def update_transaction_status(self, transaction_id: int, new_status: str) -> bool:
        """Updates transaction status ('new', 'tracked', 'deleted', 'pending')."""
        with SessionLocal() as session:
            tx = session.get(TransactionModel, transaction_id)
            if tx:
                tx.status = new_status
                session.commit()
                return True
            return False

    def assign_transaction_category(self, transaction_id: int, category_id: int) -> bool:
        """Assigns an envelope category to a transaction and updates status to 'tracked'."""
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

    def delete_by_external_id(self, external_id: str) -> bool:
        """Removes a pending or dropped bank transaction by external ID."""
        with SessionLocal() as session:
            stmt = select(TransactionModel).where(TransactionModel.external_id == external_id)
            tx = session.scalars(stmt).first()
            if tx and tx.status == "new":
                session.delete(tx)
                session.commit()
                return True
            return False