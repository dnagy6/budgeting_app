"""
File: source/services/plaid_service.py
Purpose: Plaid API client wrapper for token exchange, link tokens, and sandbox sync.
"""

import os
from dotenv import load_dotenv

from datetime import date
from decimal import Decimal
import plaid
from plaid.api import plaid_api
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest

from source.persistence.database import SessionLocal
from source.persistence.models import PlaidItemModel, PlaidAccountModel, TransactionModel
from source.persistence.repositories.plaid_repository import PlaidRepository

load_dotenv()


class PlaidService:
    def __init__(self, repository=None):
        self.repository = PlaidRepository()

        client_id = os.getenv("PLAID_CLIENT_ID")
        secret = os.getenv("PLAID_SECRET")
        env = os.getenv("PLAID_ENV", "sandbox").lower()

        host_map = {
            "sandbox": plaid.Environment.Sandbox,
            "development": plaid.Environment.Sandbox,
            "production": plaid.Environment.Production,
        }
        host = host_map.get(env, plaid.Environment.Sandbox)

        configuration = plaid.Configuration(
            host=host,
            api_key={
                "clientId": client_id,
                "secret": secret,
            }
        )
        api_client = plaid.ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)

    def create_link_token(self, user_id: str = "user_default") -> str:
        """Generates a temporary link_token to initialize Plaid Link in the browser."""
        request = LinkTokenCreateRequest(
            products=[Products("transactions")],
            client_name="Zero-Based Budgeting App",
            country_codes=[CountryCode("US")],
            language="en",
            user=LinkTokenCreateRequestUser(
                client_user_id=user_id
            )
        )
        response = self.client.link_token_create(request)
        return response["link_token"]

    def exchange_public_token(self, public_token: str) -> dict:
        """Exchanges short-lived public_token for a permanent access_token."""
        exchange_request = ItemPublicTokenExchangeRequest(
            public_token=public_token
        )
        response = self.client.item_public_token_exchange(exchange_request)
        return {
            "access_token": response["access_token"],
            "item_id": response["item_id"]
        }

    def fetch_and_save_accounts(self, access_token: str, item_id: str, institution_name: str = "Sandbox Bank"):
        """Fetches account balances from Plaid and saves Item + Accounts via repository."""
        req = AccountsGetRequest(access_token=access_token)
        resp = self.client.accounts_get(req)
        accounts_data = resp["accounts"]

        self.repository.upsert_item(item_id=item_id, access_token=access_token, institution_name=institution_name)
        return self.repository.upsert_accounts(item_id=item_id, accounts_data=accounts_data)

    def sync_transactions(self, item_id: str) -> dict:
        """
        Pulls latest transactions for an item using Plaid's cursor-based sync API,
        saves new transactions to SQLite with status='new', and updates the cursor.
        """
        # 1. Fetch item from repository (no SessionLocal needed here)
        item = self.repository.get_item_by_id(item_id)
        if not item:
            raise ValueError(f"No Plaid Item found with ID: {item_id}")

        access_token = item.access_token
        cursor = item.cursor

        added_records = []
        modified_records = []
        removed_records = []
        has_more = True

        # 2. Fetch all pages of changes from Plaid
        while has_more:
            request_args = {"access_token": access_token, "count": 100}
            if cursor:
                request_args["cursor"] = cursor

            request = TransactionsSyncRequest(**request_args)
            response = self.client.transactions_sync(request)

            added_records.extend(response["added"])
            modified_records.extend(response["modified"])
            removed_records.extend(response["removed"])

            has_more = response["has_more"]
            cursor = response["next_cursor"]

        # 3. Update cursor using repository
        self.repository.update_item_cursor(item_id, cursor)

        # 4. Persist transaction records to SQLite
        saved_count = 0
        with SessionLocal() as session:
            for tx in added_records:
                plaid_tx_id = tx["transaction_id"]

                # Deduplication check
                existing = session.query(TransactionModel).filter_by(external_id=plaid_tx_id).first()
                if existing:
                    continue

                raw_amount = Decimal(str(tx["amount"]))
                app_amount = -raw_amount

                raw_date = tx.get("authorized_date") or tx.get("date")
                if isinstance(raw_date, str):
                    tx_date = date.fromisoformat(raw_date)
                else:
                    tx_date = raw_date

                merchant = tx.get("merchant_name") or tx.get("name") or "Unknown Merchant"

                new_tx = TransactionModel(
                    amount=app_amount,
                    trans_date=tx_date,
                    category_id=None,
                    note=merchant,
                    status="new",
                    external_id=plaid_tx_id
                )
                session.add(new_tx)
                saved_count += 1

            for rm in removed_records:
                rm_id = rm["transaction_id"]
                dead_tx = session.query(TransactionModel).filter_by(external_id=rm_id).first()
                if dead_tx and dead_tx.status == "new":
                    session.delete(dead_tx)

            session.commit()

        return {
            "added_count": saved_count,
            "modified_count": len(modified_records),
            "removed_count": len(removed_records),
            "cursor": cursor,
        }