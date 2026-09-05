"""Tests for raw M5 schema and data-quality validation."""

import pandas as pd
import pytest

from src.data.validation import DataValidationError, validate_raw_data


def _valid_frames() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Create a small but relationally valid M5-shaped dataset."""
    calendar = pd.DataFrame(
        {
            "date": ["2011-01-29", "2011-01-30"],
            "wm_yr_wk": [11101, 11101],
            "weekday": ["Saturday", "Sunday"],
            "wday": [1, 2],
            "month": [1, 1],
            "year": [2011, 2011],
            "d": ["d_1", "d_2"],
            "event_name_1": [None, None],
            "event_type_1": [None, None],
            "event_name_2": [None, None],
            "event_type_2": [None, None],
            "snap_CA": [0, 0],
            "snap_TX": [0, 0],
            "snap_WI": [0, 0],
        }
    )
    sales = pd.DataFrame(
        {
            "id": ["ITEM_1_CA_1_evaluation"],
            "item_id": ["ITEM_1"],
            "dept_id": ["DEPT_1"],
            "cat_id": ["CAT_1"],
            "store_id": ["CA_1"],
            "state_id": ["CA"],
            "d_1": [1],
            "d_2": [2],
        }
    )
    prices = pd.DataFrame(
        {
            "store_id": ["CA_1"],
            "item_id": ["ITEM_1"],
            "wm_yr_wk": [11101],
            "sell_price": [2.5],
        }
    )
    return calendar, sales, prices


def test_valid_data_returns_successful_report() -> None:
    """Valid schemas and relationships should pass without warnings."""
    calendar, sales, prices = _valid_frames()

    report = validate_raw_data(calendar, sales, prices, expected_sales_days=2)

    assert report.is_valid
    assert report.errors == ()
    assert report.warnings == ()


def test_validation_aggregates_quality_errors() -> None:
    """One run should report multiple actionable data-quality failures."""
    calendar, sales, prices = _valid_frames()
    sales.loc[0, "d_2"] = -1
    prices.loc[0, "sell_price"] = 0
    prices.loc[0, "wm_yr_wk"] = 99999

    report = validate_raw_data(
        calendar,
        sales,
        prices,
        expected_sales_days=2,
        raise_on_error=False,
    )

    assert not report.is_valid
    assert any("cannot be negative" in error for error in report.errors)
    assert any("greater than 0" in error for error in report.errors)
    assert any("absent from calendar" in error for error in report.errors)


def test_validation_raises_with_actionable_summary() -> None:
    """Strict validation should stop the pipeline with all errors attached."""
    calendar, sales, prices = _valid_frames()
    calendar = calendar.drop(columns="date")

    with pytest.raises(DataValidationError, match="missing columns: date") as error:
        validate_raw_data(calendar, sales, prices, expected_sales_days=2)

    assert not error.value.report.is_valid
