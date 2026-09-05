"""Tests for the raw M5 data loaders."""

from pathlib import Path

import pandas as pd
import pytest

from src.data import load_data


def test_load_calendar_raises_clear_error_when_file_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing required file should produce an actionable error."""
    monkeypatch.setattr(load_data, "RAW_DATA_DIR", tmp_path)

    with pytest.raises(FileNotFoundError, match="calendar.csv"):
        load_data.load_calendar()


def test_load_raw_data_returns_all_three_frames(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """All expected M5 files should load into a consistently named mapping."""
    monkeypatch.setattr(load_data, "RAW_DATA_DIR", tmp_path)
    pd.DataFrame({"date": ["2011-01-29"]}).to_csv(
        tmp_path / load_data.CALENDAR_FILENAME, index=False
    )
    pd.DataFrame({"item_id": ["ITEM_1"], "d_1": [1]}).to_csv(
        tmp_path / load_data.SALES_FILENAME, index=False
    )
    pd.DataFrame({"item_id": ["ITEM_1"], "sell_price": [2.5]}).to_csv(
        tmp_path / load_data.PRICES_FILENAME, index=False
    )

    result = load_data.load_raw_data()

    assert set(result) == {"calendar", "sales", "prices"}
    assert all(isinstance(frame, pd.DataFrame) for frame in result.values())

