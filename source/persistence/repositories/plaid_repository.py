"""
File: source/persistence/repositories/plaid_repository.py
Purpose: Database CRUD operations for Plaid items (bank logins) and accounts.
"""

from typing import List, Optional
from sqlalchemy import select
from source.persistence.database import SessionLocal
from source.persistence.models import PlaidItemModel, PlaidAccountModel


class PlaidRepository:
    """Manages persistence for connected financial institutions and account balances."""

    def get_all_items(self) -> List[PlaidItemModel]:
        """Returns all connected bank institutions."""
        with SessionLocal() as session:
            stmt = select(PlaidItemModel)
            return list(session.scalars(stmt).all())

    def get_item_by_id(self, item_id: str) -> Optional[PlaidItemModel]:
        """Fetches a specific institution item by its Plaid item_id."""
        with SessionLocal() as session:
            stmt = select(PlaidItemModel).where(PlaidItemModel.item_id == item_id)
            return session.scalars(stmt).first()

    def upsert_item(self, item_id: str, access_token: str, institution_name: str = "Connected Bank") -> PlaidItemModel:
        """Creates or updates a Plaid institution connection."""
        with SessionLocal() as session:
            item = session.query(PlaidItemModel).filter_by(item_id=item_id).first()
            if not item:
                item = PlaidItemModel(
                    item_id=item_id,
                    access_token=access_token,
                    institution_name=institution_name,
                    status="active"
                )
                session.add(item)
            else:
                item.access_token = access_token
                item.institution_name = institution_name
                item.status = "active"
            session.commit()
            session.refresh(item)
            return item

    def update_item_cursor(self, item_id: str, cursor: str) -> bool:
        """Updates the delta sync cursor for an institution."""
        with SessionLocal() as session:
            item = session.query(PlaidItemModel).filter_by(item_id=item_id).first()
            if item:
                item.cursor = cursor
                session.commit()
                return True
            return False

    def delete_item(self, item_id: str) -> bool:
        """Deletes an institution connection (cascades to all child accounts)."""
        with SessionLocal() as session:
            item = session.query(PlaidItemModel).filter_by(item_id=item_id).first()
            if item:
                session.delete(item)
                session.commit()
                return True
            return False

    def get_all_accounts(self) -> List[PlaidAccountModel]:
        """Returns all accounts across all linked institutions."""
        with SessionLocal() as session:
            stmt = select(PlaidAccountModel)
            return list(session.scalars(stmt).all())

    def upsert_accounts(self, item_id: str, accounts_data: list) -> int:
        """Saves or updates account snapshots returned from Plaid accounts_get."""
        with SessionLocal() as session:
            for acc in accounts_data:
                existing = session.query(PlaidAccountModel).filter_by(account_id=acc["account_id"]).first()
                curr_bal = float(acc["balances"]["current"] or 0.0)
                avail_bal = float(acc["balances"]["available"] or curr_bal)

                if existing:
                    existing.current_balance = curr_bal
                    existing.available_balance = avail_bal
                    existing.name = acc["name"]
                else:
                    new_acc = PlaidAccountModel(
                        item_id=item_id,
                        account_id=acc["account_id"],
                        name=acc["name"],
                        official_name=acc.get("official_name"),
                        mask=acc.get("mask"),
                        type=str(acc["type"]),
                        subtype=str(acc.get("subtype")),
                        current_balance=curr_bal,
                        available_balance=avail_bal
                    )
                    session.add(new_acc)
            session.commit()
        return len(accounts_data)