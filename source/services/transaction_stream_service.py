"""
File: source/services/transaction_stream_service.py
Purpose: Ingestion pipeline for processing, deduplicating, and auto-matching incoming bank feeds.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

# Domain
from source.domain.view_models import TransactionStreamViewState

#Persistence
from source.persistence.models import CategoryModel
from source.persistence.repository import BudgetRepository

#Services
from source.services.mock_stream_generator import MockStreamGenerator


class TransactionStreamService:
    def __init__(self, repository: BudgetRepository):
        self.repository = repository

    def ingest_payload(self, raw_transactions: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Processes a batch of transactions from a webhook or mock feed.
        Returns metrics for ingested, updated, and skipped items.
        """
        stats = {"ingested": 0, "updated": 0, "skipped": 0}
        all_categories = self.repository.get_all_categories(include_archived=False)

        for item in raw_transactions:
            ext_id = item.get("external_id")
            raw_amt = item.get("amount", 0.0)
            amount = Decimal(str(raw_amt))
            note = item.get("note", "").strip()
            is_pending = item.get("pending", False)

            # Parse transaction date
            raw_date = item.get("date")
            if isinstance(raw_date, str):
                try:
                    trans_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
                except ValueError:
                    trans_date = date.today()
            elif isinstance(raw_date, date):
                trans_date = raw_date
            else:
                trans_date = date.today()

            target_status = "pending" if is_pending else "new"

            # 1. Deduplication & State Transition Check
            if ext_id:
                existing_tx = self.repository.get_transaction_by_external_id(ext_id)
                if existing_tx:
                    # If transaction was pending and is now settled, promote to 'new' or keep 'tracked'
                    if existing_tx.status == "pending" and not is_pending:
                        new_status = "tracked" if existing_tx.category_id else "new"
                        self.repository.update_transaction_status(existing_tx.id, new_status)
                        stats["updated"] += 1
                    else:
                        stats["skipped"] += 1
                    continue

            # 2. Heuristic Auto-Categorization
            matched_cat_id = self._match_category(note, all_categories)

            # If auto-matched and settled, it can default to "tracked" or stay "new" for confirmation
            initial_status = "pending" if is_pending else "new"

            # 3. Persist to SQLite
            self.repository.add_transaction(
                amount=amount,
                trans_date=trans_date,
                category_id=matched_cat_id,
                note=note,
                status=initial_status,
                external_id=ext_id
            )
            stats["ingested"] += 1

        return stats

    def _match_category(self, note: str, categories: List[CategoryModel]) -> Optional[int]:
        """Matches transaction merchant names against envelope keywords."""
        note_lower = note.lower()

        # Direct name match against existing envelopes
        for cat in categories:
            cat_name = cat.name.lower()
            if cat_name in note_lower or note_lower in cat_name:
                return cat.id

        # Common merchant rules
        merchant_rules = {
            "rent": ["apartment", "landlord", "leasing", "property", "rent"],
            "groceries": ["kroger", "trader joe", "whole foods", "aldi", "safeway", "publix", "costco", "market"],
            "utilities": ["electric", "water", "power", "energy", "columbia gas", "spectrum", "at&t"],
            "insurance": ["geico", "state farm", "progressive", "liberty mutual", "allstate"],
            "dining": ["uber eats", "doordash", "chipotle", "starbucks", "mcdonald", "restaurant", "cafe"],
            "income": ["payroll", "direct deposit", "gusto", "adp", "stripe payout", "employer"],
        }

        for rule_category, keywords in merchant_rules.items():
            if any(kw in note_lower for kw in keywords):
                for cat in categories:
                    if rule_category in cat.name.lower():
                        return cat.id

        return None

    # State Management

    def track_transaction(self, tx_id: int, category_id: int):
        """Assigns an envelope category and marks the transaction as tracked."""
        self.repository.assign_transaction_category(tx_id, category_id)
        self.repository.update_transaction_status(tx_id, "tracked")

    def soft_delete_transaction(self, tx_id: int):
        """Moves a transaction to the deleted tab without permanently removing it."""
        self.repository.update_transaction_status(tx_id, "deleted")

    def restore_transaction(self, tx_id: int):
        """Restores a soft-deleted transaction back to active tracked status."""
        self.repository.update_transaction_status(tx_id, "tracked")

    def hard_delete_transaction(self, tx_id: int):
        """Permanently removes a transaction from the database."""
        self.repository.hard_delete_transaction(tx_id)


    # Transaction Counter

    def get_stream_view_state(self, budget_service, year: int, month: int, active_tab: str) -> TransactionStreamViewState:
        """Aggregates all necessary data for the transaction panel into a single reusable view state."""
        counts = budget_service.get_transaction_status_counts(year, month)
        transactions = budget_service.get_transactions_by_status(year, month, status=active_tab)
        
        all_categories = self.repository.get_all_categories(include_archived=False)
        
        cat_id_to_name = {c.id: c.name for c in all_categories}
        cat_name_to_id = {c.name: c.id for c in all_categories}
        
        return TransactionStreamViewState(
            counts=counts,
            transactions=transactions,
            cat_id_to_name=cat_id_to_name,
            cat_name_to_id=cat_name_to_id
        )

    #Bank Syncing (Currently a Simulation)

    def simulate_sync(self, year: int, month: int, count: int = 4):
        """Simulates a bank feed webhook payload and processes the batch."""
        batch = MockStreamGenerator.generate_batch(
            count=count,
            year=year,
            month=month
        )
        return self.ingest_payload(batch)
