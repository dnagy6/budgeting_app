"""
File: source/domain/view_models.py
Purpose: Reusable Data Transfer Objects (DTOs) and View Models to decouple UI components from raw database queries.
"""

from dataclasses import dataclass
from typing import Dict, List, Any

@dataclass
class TransactionStreamViewState:
    """Unified state payload for rendering the transaction stream and its tabs."""
    counts: Dict[str, int]
    transactions: List[Any]
    cat_id_to_name: Dict[int, str]
    cat_name_to_id: Dict[str, int]