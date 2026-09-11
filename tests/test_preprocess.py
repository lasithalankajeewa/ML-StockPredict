"""Tests for memory-conscious preprocessing helpers."""

import pandas as pd
import pytest

from src.data.preprocess import reshape_sales_to_long, select_store_subset


def _raw_data() -> dict[str, pd.DataFrame]:
    """Return a small set of M5-shaped DataFrames for subset tests."""
    return {
        "calendar": pd.DataFrame({"d": ["d_1", "d_2"]}),
        "sales": pd.DataFrame(
            {
                "store_id": ["CA_1", "CA_1", "TX_1"],
                "item_id": ["ITEM_1", "ITEM_2", "ITEM_1"],
                "d_1": [1, 2, 3],
            }
        ),
        "prices": pd.DataFrame(
            {
                "store_id": ["CA_1", "TX_1"],
                "item_id": ["ITEM_1", "ITEM_1"],
                "sell_price": [2.5, 2.75],
            }
        ),
    }


def test_select_store_subset_filters_sales_and_prices() -> None:
    """Only the chosen store should remain in store-specific tables."""
    raw_data = _raw_data()

    result = select_store_subset(raw_data, store_id="CA_1")

    assert result["sales"]["store_id"].unique().tolist() == ["CA_1"]
    assert result["prices"]["store_id"].unique().tolist() == ["CA_1"]
    assert len(result["sales"]) == 2
    assert len(raw_data["sales"]) == 3
    assert result["calendar"] is raw_data["calendar"]


def test_select_store_subset_rejects_unknown_store() -> None:
    """An unknown store should produce an actionable error."""
    with pytest.raises(ValueError, match="Available stores: CA_1, TX_1"):
        select_store_subset(_raw_data(), store_id="WI_9")


def test_select_store_subset_requires_all_datasets() -> None:
    """The helper should reject an incomplete raw-data mapping."""
    raw_data = _raw_data()
    del raw_data["prices"]

    with pytest.raises(ValueError, match="Missing required datasets: prices"):
        select_store_subset(raw_data)


def test_reshape_sales_to_long_preserves_identifiers_and_day_order() -> None:
    """Wide demand columns should become ordered day and demand rows."""
    sales = pd.DataFrame(
        {
            "id": ["ITEM_1_CA_1_evaluation", "ITEM_2_CA_1_evaluation"],
            "item_id": ["ITEM_1", "ITEM_2"],
            "dept_id": ["DEPT_1", "DEPT_1"],
            "cat_id": ["CAT_1", "CAT_1"],
            "store_id": ["CA_1", "CA_1"],
            "state_id": ["CA", "CA"],
            "d_2": [2, 4],
            "d_1": [1, 3],
        }
    )

    result = reshape_sales_to_long(sales)

    assert result.columns.tolist() == [
        "id",
        "item_id",
        "dept_id",
        "cat_id",
        "store_id",
        "state_id",
        "d",
        "demand",
    ]
    assert result["d"].astype("string").tolist() == [
        "d_1",
        "d_1",
        "d_2",
        "d_2",
    ]
    assert result["demand"].tolist() == [1, 3, 2, 4]
    assert isinstance(result["d"].dtype, pd.CategoricalDtype)
    assert result["d"].cat.ordered
    assert result["demand"].dtype.kind == "u"
    assert "d_1" in sales.columns


def test_reshape_sales_to_long_rejects_invalid_demand() -> None:
    """Invalid demand should fail before a large long table is allocated."""
    sales = pd.DataFrame(
        {
            "id": ["ITEM_1_CA_1_evaluation"],
            "item_id": ["ITEM_1"],
            "dept_id": ["DEPT_1"],
            "cat_id": ["CAT_1"],
            "store_id": ["CA_1"],
            "state_id": ["CA"],
            "d_1": [-1],
        }
    )

    with pytest.raises(ValueError, match="cannot be negative"):
        reshape_sales_to_long(sales)
