"""Demand prediction service placeholder.

Model loading and prediction will be added only after a trained model and its
preprocessing artifacts are versioned and available.
"""

from collections.abc import Mapping
from typing import Any


class DemandPredictor:
    """Future interface for loading a model and forecasting seven-day demand."""

    def predict(self, features: Mapping[str, Any]) -> list[float]:
        """Return a seven-day demand forecast in a future milestone."""
        raise NotImplementedError("Demand prediction is not implemented yet.")

