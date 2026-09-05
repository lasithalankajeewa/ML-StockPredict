"""Reusable loaders for the raw M5 Forecasting dataset files."""

from pathlib import Path

import pandas as pd

from src.config import (
    CALENDAR_FILENAME,
    PRICES_FILENAME,
    RAW_DATA_DIR,
    SALES_FILENAME,
)


def _read_required_csv(path: Path) -> pd.DataFrame:
    """Read a required CSV file or raise an actionable error.

    Args:
        path: Path to the CSV file.

    Returns:
        The CSV contents as a pandas DataFrame.

    Raises:
        FileNotFoundError: If the required file does not exist.
    """
    if not path.is_file():
        raise FileNotFoundError(
            f"Required M5 dataset file not found: {path}. "
            "Download it manually and place it in data/raw/."
        )

    return pd.read_csv(path)


def load_calendar() -> pd.DataFrame:
    """Load the M5 calendar data."""
    return _read_required_csv(RAW_DATA_DIR / CALENDAR_FILENAME)


def load_sales() -> pd.DataFrame:
    """Load the M5 evaluation-period sales data."""
    return _read_required_csv(RAW_DATA_DIR / SALES_FILENAME)


def load_prices() -> pd.DataFrame:
    """Load the M5 weekly selling-price data."""
    return _read_required_csv(RAW_DATA_DIR / PRICES_FILENAME)


def load_raw_data() -> dict[str, pd.DataFrame]:
    """Load all required raw M5 files.

    Returns:
        A mapping containing the calendar, sales, and prices DataFrames.
    """
    return {
        "calendar": load_calendar(),
        "sales": load_sales(),
        "prices": load_prices(),
    }

