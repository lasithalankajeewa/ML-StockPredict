"""Tests for per-store feature partition orchestration."""

import pandas as pd
import pytest

from src.data.pipeline import build_feature_partitions, discover_store_ids


def _raw_data(days: int = 40) -> dict[str, pd.DataFrame]:
    dates = pd.date_range("2020-01-01", periods=days, freq="D")
    day_columns = {f"d_{day + 1}": [day % 5] for day in range(days)}
    sales = pd.DataFrame(
        {
            "id": ["ITEM_1_CA_1_evaluation"],
            "item_id": ["ITEM_1"],
            "dept_id": ["DEPT_1"],
            "cat_id": ["CAT_1"],
            "store_id": ["CA_1"],
            "state_id": ["CA"],
            **day_columns,
        }
    )
    calendar = pd.DataFrame(
        {
            "d": [f"d_{day + 1}" for day in range(days)],
            "date": dates,
            "wm_yr_wk": [100 + day // 7 for day in range(days)],
            "weekday": dates.day_name(),
            "wday": dates.dayofweek + 1,
            "month": dates.month,
            "year": dates.year,
            "event_name_1": None,
            "event_type_1": None,
            "event_name_2": None,
            "event_type_2": None,
            "snap_CA": 0,
            "snap_TX": 0,
            "snap_WI": 0,
        }
    )
    prices = pd.DataFrame(
        {
            "store_id": "CA_1",
            "item_id": "ITEM_1",
            "wm_yr_wk": sorted(calendar["wm_yr_wk"].unique()),
            "sell_price": 2.5,
        }
    )
    return {"calendar": calendar, "sales": sales, "prices": prices}


def test_extra_calendar_forecast_days_do_not_break_merge(tmp_path) -> None:
    """M5 calendar days beyond the sales history should be ignored safely."""
    raw_data = _raw_data()
    extra = raw_data["calendar"].iloc[[-1]].copy()
    extra["d"] = "d_41"
    extra["date"] += pd.Timedelta(days=1)
    raw_data["calendar"] = pd.concat(
        [raw_data["calendar"], extra], ignore_index=True
    )

    result = build_feature_partitions(
        raw_data,
        output_dir=tmp_path,
    )
    assert result.loc[0, "feature_rows"] == 5


def test_build_feature_partitions_writes_parquet_and_manifest(tmp_path) -> None:
    """A requested store should be built and saved independently."""
    result = build_feature_partitions(_raw_data(), output_dir=tmp_path)
    feature_path = tmp_path / "store_id=CA_1" / "features.parquet"

    assert feature_path.is_file()
    assert (tmp_path / "manifest.csv").is_file()
    assert result.loc[0, "store_id"] == "CA_1"
    saved = pd.read_parquet(feature_path)
    assert saved["store_id"].astype("string").unique().tolist() == ["CA_1"]
    assert saved[["lag_28", "target_7d"]].notna().all(axis=None)


def test_existing_partition_requires_explicit_overwrite(tmp_path) -> None:
    """Reruns should not replace generated data accidentally."""
    raw_data = _raw_data()
    build_feature_partitions(raw_data, output_dir=tmp_path)

    with pytest.raises(FileExistsError, match="--overwrite"):
        build_feature_partitions(raw_data, output_dir=tmp_path)


def test_discover_store_ids_sorts_stores() -> None:
    sales = pd.DataFrame({"store_id": ["TX_1", "CA_1", "TX_1"]})
    assert discover_store_ids(sales) == ["CA_1", "TX_1"]
