"""Inventory decision-support placeholder.

Stock risk, safety stock, and reorder recommendations will be introduced after
forecasting behavior and inventory assumptions are validated.
"""

from collections.abc import Sequence
from typing import Any


def calculate_inventory_recommendation(
    predicted_demand: Sequence[float],
    current_inventory: float,
) -> dict[str, Any]:
    """Calculate an inventory recommendation in a future milestone."""
    raise NotImplementedError("Inventory recommendations are not implemented yet.")

