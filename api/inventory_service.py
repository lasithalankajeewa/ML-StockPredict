"""Convert a seven-day demand forecast into a simple inventory action."""

import math
from typing import Any


def calculate_inventory_recommendation(
    predicted_demand: float,
    current_stock: int,
    safety_stock: int,
) -> dict[str, Any]:
    """Round to units and replenish forecast demand plus the safety buffer."""
    if not math.isfinite(predicted_demand):
        raise ValueError("Predicted demand must be finite.")
    if current_stock < 0 or safety_stock < 0:
        raise ValueError("Stock values must be nonnegative.")

    demand_units = max(0, math.ceil(predicted_demand))
    recommended_reorder = max(0, demand_units + safety_stock - current_stock)
    if current_stock < demand_units:
        risk_level = "HIGH"
    elif current_stock < demand_units + safety_stock:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "predicted_demand_7_days": demand_units,
        "current_stock": current_stock,
        "safety_stock": safety_stock,
        "recommended_reorder": recommended_reorder,
        "risk_level": risk_level,
    }
