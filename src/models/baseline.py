"""Seasonal-naive baseline used for seven-day demand evaluation."""

from __future__ import annotations

import numpy as np
import pandas as pd


def seasonal_naive_predict(features: pd.DataFrame) -> np.ndarray:
    """Predict next-week demand with observed demand from the previous week."""
    if "sales_sum_7" not in features:
        raise ValueError("The seasonal baseline requires the sales_sum_7 feature.")
    values = features["sales_sum_7"].to_numpy(dtype=np.float32)
    if not np.isfinite(values).all():
        raise ValueError("sales_sum_7 contains non-finite values.")
    return np.maximum(values, 0)
