"""
File: source/services/plaid_service.py
Purpose: Plaid API client wrapper for token exchange, link tokens, and sandbox sync.
"""

import os
from dotenv import load_dotenv
import plaid
from plaid.api import plaid_api
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.accounts_get_request import AccountsGetRequest

from source.persistence.database import SessionLocal
from source.persistence.models import PlaidItemModel, PlaidAccountModel

load_dotenv()


class PlaidService:
    def __init__(self, repository=None):
        self.repository = repository

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
        """Fetches account balances from Plaid and saves Item + Accounts in SQLite."""
        # Fetch live account structures from Plaid
        req = AccountsGetRequest(access_token=access_token)
        resp = self.client.accounts_get(req)
        accounts_data = resp["accounts"]

        with SessionLocal() as session:
            # Upsert Plaid Item
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
                item.status = "active"

            # Upsert individual accounts (Checking, Savings, Credit)
            for acc in accounts_data:
                existing_acc = session.query(PlaidAccountModel).filter_by(account_id=acc["account_id"]).first()
                curr_bal = float(acc["balances"]["current"] or 0.0)
                avail_bal = float(acc["balances"]["available"] or curr_bal)

                if existing_acc:
                    existing_acc.current_balance = curr_bal
                    existing_acc.available_balance = avail_bal
                    existing_acc.name = acc["name"]
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