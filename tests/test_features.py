"""Tests for leakage-safe time-series feature engineering."""

import numpy as np
import pandas as pd
import pytest

from src.data.features import build_features, validate_feature_frame


def _merged_panel(days: int = 50) -> pd.DataFrame:
    dates = pd.date_range("2020-01-01", periods=days, freq="D")
    frames = []
    for store_id, offset, price_start in (("CA_1", 0, 0), ("TX_1", 100, 5)):
        frame = pd.DataFrame(
            {
                "store_id": store_id,
                "item_id": "ITEM_1",
                "date": dates,
                "demand": np.arange(days) + offset,
                "sell_price": 2.0,
                "month": dates.month,
                "event_name_1": "NoEvent",
                "event_name_2": "NoEvent",
            }
        )
        frame.loc[: price_start - 1, "sell_price"] = np.nan
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def test_features_do_not_leak_between_stores() -> None:
    """The same item in two stores must retain independent history."""
    result = build_features(_merged_panel(), drop_incomplete=False)

    tx = result.loc[result["store_id"] == "TX_1"].reset_index(drop=True)
    assert tx.loc[0, "date"] == pd.Timestamp("2020-01-06")
    assert tx.loc[0, "days_since_release"] == 0
    assert pd.isna(tx.loc[0, "lag_1"])
    assert tx.loc[1, "lag_1"] == 105
    assert tx.loc[28, "rolling_mean_28"] == pytest.approx(np.mean(range(105, 133)))


def test_target_is_sum_of_next_seven_days() -> None:
    """The label must exclude today's demand and contain seven future days."""
    result = build_features(_merged_panel(), drop_incomplete=False)
    ca = result.loc[result["store_id"] == "CA_1"].reset_index(drop=True)

    assert ca.loc[0, "target_7d"] == sum(range(1, 8))
    assert ca.loc[10, "target_7d"] == sum(range(11, 18))
    assert ca["target_7d"].tail(7).isna().all()


def test_model_frame_has_complete_features() -> None:
    """Default output should contain only trainable, validated rows."""
    result = build_features(_merged_panel())

    validate_feature_frame(result)
    assert result.groupby(["store_id", "item_id"], observed=True).size().to_dict() == {
        ("CA_1", "ITEM_1"): 15,
        ("TX_1", "ITEM_1"): 10,
    }


def test_never_priced_series_is_rejected() -> None:
    """A series with no price cannot safely produce price features."""
    panel = _merged_panel()
    panel.loc[panel["store_id"] == "TX_1", "sell_price"] = np.nan

    with pytest.raises(ValueError, match="1 item-store series"):
        build_features(panel)
