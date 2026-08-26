"""
File: source/services/mock_stream_generator.py
Purpose: Generates realistic mock bank transaction payloads simulating Plaid webhooks.
"""

import random
import uuid
from datetime import date
from typing import Any, Dict, List


MOCK_MERCHANTS = [
    {"note": "Kroger Grocery Store", "type": "expense", "amount_range": (35.0, 185.0)},
    {"note": "Trader Joe's", "type": "expense", "amount_range": (25.0, 95.0)},
    {"note": "Chipotle Mexican Grill", "type": "expense", "amount_range": (12.0, 32.0)},
    {"note": "Starbucks Coffee", "type": "expense", "amount_range": (4.50, 15.0)},
    {"note": "Shell Oil Gas Station", "type": "expense", "amount_range": (30.0, 65.0)},
    {"note": "Electric Utility Bill", "type": "expense", "amount_range": (75.0, 160.0)},
    {"note": "Spectrum Internet", "type": "expense", "amount_range": (69.99, 89.99)},
    {"note": "Netflix Subscription", "type": "expense", "amount_range": (15.49, 22.99)},
    {"note": "Target Superstore", "type": "expense", "amount_range": (18.0, 140.0)},
    {"note": "State Farm Insurance", "type": "expense", "amount_range": (120.0, 160.0)},
    {"note": "Payroll Direct Deposit", "type": "income", "amount_range": (1800.0, 2400.0)},
]


class MockStreamGenerator:
    @staticmethod
    def generate_batch(count: int = 4, year: int = 2026, month: int = 8) -> List[Dict[str, Any]]:
        """Generates a batch of randomized transaction payloads for a specific month and year."""
        batch = []
        for _ in range(count):
            template = random.choice(MOCK_MERCHANTS)
            min_amt, max_amt = template["amount_range"]
            amount = round(random.uniform(min_amt, max_amt), 2)
            
            # Choose a day within the month
            day = random.randint(1, 28)
            tx_date = date(year, month, day).strftime("%Y-%m-%d")
            
            # ~25% chance of being marked as pending
            is_pending = random.random() < 0.25
            
            batch.append({
                "external_id": f"plaid_{uuid.uuid4().hex[:12]}",
                "amount": amount,
                "date": tx_date,
                "note": template["note"],
                "pending": is_pending
            })
            
        return batch