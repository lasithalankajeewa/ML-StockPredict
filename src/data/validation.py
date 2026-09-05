"""Schema and data-quality validation for the raw M5 dataset."""

import re
from dataclasses import dataclass

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype


EXPECTED_EVALUATION_DAYS = 1_941
DAY_COLUMN_PATTERN = re.compile(r"^d_(\d+)$")

CALENDAR_COLUMNS = {
    "date",
    "wm_yr_wk",
    "weekday",
    "wday",
    "month",
    "year",
    "d",
    "event_name_1",
    "event_type_1",
    "event_name_2",
    "event_type_2",
    "snap_CA",
    "snap_TX",
    "snap_WI",
}
SALES_ID_COLUMNS = {
    "id",
    "item_id",
    "dept_id",
    "cat_id",
    "store_id",
    "state_id",
}
PRICE_COLUMNS = {"store_id", "item_id", "wm_yr_wk", "sell_price"}


@dataclass(frozen=True)
class ValidationReport:
    """Result of validating the three raw M5 DataFrames."""

    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        """Return whether validation found no blocking errors."""
        return not self.errors

    def summary(self) -> str:
        """Return a human-readable validation summary."""
        if self.is_valid:
            result = "M5 raw-data validation passed."
        else:
            details = "\n".join(f"- {message}" for message in self.errors)
            result = f"M5 raw-data validation failed:\n{details}"

        if self.warnings:
            warning_details = "\n".join(
                f"- {message}" for message in self.warnings
            )
            result = f"{result}\nWarnings:\n{warning_details}"
        return result


class DataValidationError(ValueError):
    """Raised when raw M5 data fails schema or quality validation."""

    def __init__(self, report: ValidationReport) -> None:
        super().__init__(report.summary())
        self.report = report


def _missing_columns(frame: pd.DataFrame, required: set[str]) -> list[str]:
    """Return required columns that are absent from a DataFrame."""
    return sorted(required.difference(frame.columns))


def _has_non_finite_values(frame: pd.DataFrame, columns: list[str]) -> bool:
    """Check numeric columns for positive or negative infinity efficiently."""
    return any(
        np.isinf(frame[column].to_numpy(copy=False)).any() for column in columns
    )


def _validate_calendar(
    calendar: pd.DataFrame,
    errors: list[str],
    warnings: list[str],
) -> None:
    """Validate the calendar schema and calendar-specific quality rules."""
    if calendar.empty:
        errors.append("calendar.csv contains no rows.")
        return

    missing = _missing_columns(calendar, CALENDAR_COLUMNS)
    if missing:
        errors.append(f"calendar.csv is missing columns: {', '.join(missing)}.")
        return

    unexpected = sorted(set(calendar.columns).difference(CALENDAR_COLUMNS))
    if unexpected:
        warnings.append(
            f"calendar.csv has unexpected columns: {', '.join(unexpected)}."
        )

    required_values = [
        "date",
        "wm_yr_wk",
        "weekday",
        "wday",
        "month",
        "year",
        "d",
        "snap_CA",
        "snap_TX",
        "snap_WI",
    ]
    if calendar[required_values].isna().any(axis=None):
        errors.append("calendar.csv has missing values in required columns.")

    parsed_dates = pd.to_datetime(calendar["date"], errors="coerce")
    if parsed_dates.isna().any():
        errors.append("calendar.csv contains invalid values in date.")
    elif parsed_dates.duplicated().any():
        errors.append("calendar.csv contains duplicate dates.")

    if calendar["d"].duplicated().any():
        errors.append("calendar.csv contains duplicate d identifiers.")

    day_numbers = calendar["d"].astype("string").str.extract(
        DAY_COLUMN_PATTERN, expand=False
    )
    if day_numbers.isna().any():
        errors.append("calendar.csv d values must use the d_<number> format.")
    elif not parsed_dates.isna().any():
        numeric_days = day_numbers.astype(int)
        ordered_day_numbers = numeric_days.sort_values()
        if (
            ordered_day_numbers.iloc[0] < 1
            or not ordered_day_numbers.diff().dropna().eq(1).all()
        ):
            errors.append(
                "calendar.csv d identifiers must be a consecutive sequence "
                "starting at 1 or later."
            )
        order = ordered_day_numbers.index
        ordered_dates = parsed_dates.loc[order]
        if not ordered_dates.diff().dropna().eq(pd.Timedelta(days=1)).all():
            errors.append(
                "calendar.csv day identifiers do not map to consecutive dates."
            )

    for column in ("wm_yr_wk", "year"):
        if not is_numeric_dtype(calendar[column]):
            errors.append(f"calendar.csv {column} must be numeric.")

    for column, minimum, maximum in (
        ("wday", 1, 7),
        ("month", 1, 12),
    ):
        if not is_numeric_dtype(calendar[column]):
            errors.append(f"calendar.csv {column} must be numeric.")
        elif not calendar[column].between(minimum, maximum).all():
            errors.append(
                f"calendar.csv {column} values must be between {minimum} and "
                f"{maximum}."
            )

    for column in ("snap_CA", "snap_TX", "snap_WI"):
        if not calendar[column].dropna().isin((0, 1)).all():
            errors.append(f"calendar.csv {column} must contain only 0 or 1.")

    for suffix in ("1", "2"):
        name_missing = calendar[f"event_name_{suffix}"].isna()
        type_missing = calendar[f"event_type_{suffix}"].isna()
        if (name_missing != type_missing).any():
            errors.append(
                f"calendar.csv event_name_{suffix} and event_type_{suffix} "
                "must be populated together."
            )


def _validate_sales(
    sales: pd.DataFrame,
    expected_sales_days: int,
    errors: list[str],
    warnings: list[str],
) -> list[str]:
    """Validate sales schema and return ordered daily-demand column names."""
    if sales.empty:
        errors.append("sales_train_evaluation.csv contains no rows.")
        return []

    missing = _missing_columns(sales, SALES_ID_COLUMNS)
    if missing:
        errors.append(
            "sales_train_evaluation.csv is missing columns: "
            f"{', '.join(missing)}."
        )
        return []

    day_columns_by_number = {
        int(match.group(1)): column
        for column in sales.columns
        if (match := DAY_COLUMN_PATTERN.fullmatch(str(column)))
    }
    expected_numbers = set(range(1, expected_sales_days + 1))
    actual_numbers = set(day_columns_by_number)
    missing_days = sorted(expected_numbers.difference(actual_numbers))
    extra_days = sorted(actual_numbers.difference(expected_numbers))
    if missing_days or extra_days:
        details: list[str] = []
        if missing_days:
            preview = ", ".join(f"d_{number}" for number in missing_days[:5])
            details.append(
                f"missing {len(missing_days)} day columns (first: {preview})"
            )
        if extra_days:
            preview = ", ".join(f"d_{number}" for number in extra_days[:5])
            details.append(f"found unexpected day columns (first: {preview})")
        errors.append(
            "sales_train_evaluation.csv must contain consecutive demand columns "
            f"d_1 through d_{expected_sales_days}; {'; '.join(details)}."
        )

    day_columns = [
        day_columns_by_number[number]
        for number in sorted(actual_numbers.intersection(expected_numbers))
    ]
    actual_day_columns = set(day_columns_by_number.values())
    unexpected = sorted(
        set(sales.columns)
        .difference(SALES_ID_COLUMNS)
        .difference(actual_day_columns)
    )
    if unexpected:
        warnings.append(
            "sales_train_evaluation.csv has unexpected non-demand columns: "
            f"{', '.join(unexpected)}."
        )

    identifier_columns = sorted(SALES_ID_COLUMNS)
    if sales[identifier_columns].isna().any(axis=None):
        errors.append(
            "sales_train_evaluation.csv has missing product hierarchy identifiers."
        )
    if sales["id"].duplicated().any():
        errors.append("sales_train_evaluation.csv contains duplicate id values.")
    if sales.duplicated(subset=["item_id", "store_id"]).any():
        errors.append(
            "sales_train_evaluation.csv contains duplicate item_id/store_id rows."
        )
    if not sales["id"].astype("string").str.endswith("_evaluation").all():
        warnings.append(
            "Some sales ids do not end in _evaluation; confirm the evaluation file "
            "was supplied."
        )

    non_numeric_days = [
        column for column in day_columns if not is_numeric_dtype(sales[column])
    ]
    if non_numeric_days:
        preview = ", ".join(non_numeric_days[:5])
        errors.append(
            "sales_train_evaluation.csv demand columns must be numeric; invalid "
            f"columns include: {preview}."
        )
    elif day_columns:
        demand = sales[day_columns]
        if demand.isna().any(axis=None):
            errors.append(
                "sales_train_evaluation.csv demand columns contain missing values."
            )
        if (demand < 0).any(axis=None):
            errors.append(
                "sales_train_evaluation.csv demand values cannot be negative."
            )
        if _has_non_finite_values(sales, day_columns):
            errors.append(
                "sales_train_evaluation.csv demand values must be finite."
            )

    return day_columns


def _validate_prices(
    prices: pd.DataFrame,
    errors: list[str],
    warnings: list[str],
) -> None:
    """Validate selling-price schema and price-specific quality rules."""
    if prices.empty:
        errors.append("sell_prices.csv contains no rows.")
        return

    missing = _missing_columns(prices, PRICE_COLUMNS)
    if missing:
        errors.append(f"sell_prices.csv is missing columns: {', '.join(missing)}.")
        return

    unexpected = sorted(set(prices.columns).difference(PRICE_COLUMNS))
    if unexpected:
        warnings.append(
            f"sell_prices.csv has unexpected columns: {', '.join(unexpected)}."
        )

    key_columns = ["store_id", "item_id", "wm_yr_wk"]
    if prices[list(PRICE_COLUMNS)].isna().any(axis=None):
        errors.append("sell_prices.csv has missing values in required columns.")
    if prices.duplicated(subset=key_columns).any():
        errors.append(
            "sell_prices.csv contains duplicate store_id/item_id/wm_yr_wk rows."
        )
    if not is_numeric_dtype(prices["wm_yr_wk"]):
        errors.append("sell_prices.csv wm_yr_wk must be numeric.")
    if not is_numeric_dtype(prices["sell_price"]):
        errors.append("sell_prices.csv sell_price must be numeric.")
    else:
        if not np.isfinite(prices["sell_price"].to_numpy(copy=False)).all():
            errors.append("sell_prices.csv sell_price values must be finite.")
        if (prices["sell_price"] <= 0).any():
            errors.append("sell_prices.csv sell_price values must be greater than 0.")


def _validate_relationships(
    calendar: pd.DataFrame,
    sales: pd.DataFrame,
    prices: pd.DataFrame,
    day_columns: list[str],
    errors: list[str],
) -> None:
    """Validate key relationships among the three M5 files."""
    if "d" in calendar and day_columns:
        unknown_days = sorted(set(day_columns).difference(calendar["d"].dropna()))
        if unknown_days:
            errors.append(
                "Sales demand columns are absent from calendar.csv: "
                f"{', '.join(unknown_days[:5])}."
            )

    if (
        "wm_yr_wk" in calendar
        and "wm_yr_wk" in prices
        and is_numeric_dtype(calendar["wm_yr_wk"])
        and is_numeric_dtype(prices["wm_yr_wk"])
    ):
        unknown_weeks = set(prices["wm_yr_wk"].dropna()).difference(
            calendar["wm_yr_wk"].dropna()
        )
        if unknown_weeks:
            preview = ", ".join(map(str, sorted(unknown_weeks)[:5]))
            errors.append(
                "sell_prices.csv contains wm_yr_wk values absent from calendar.csv: "
                f"{preview}."
            )

    relationship_columns = {"item_id", "store_id"}
    if relationship_columns.issubset(sales) and relationship_columns.issubset(prices):
        sales_keys = pd.MultiIndex.from_frame(
            sales[["item_id", "store_id"]].drop_duplicates()
        )
        price_keys = pd.MultiIndex.from_frame(
            prices[["item_id", "store_id"]].drop_duplicates()
        )
        unknown_price_keys = price_keys.difference(sales_keys)
        if len(unknown_price_keys):
            errors.append(
                "sell_prices.csv contains item/store combinations absent from the "
                f"sales file ({len(unknown_price_keys)} combinations)."
            )
        missing_price_keys = sales_keys.difference(price_keys)
        if len(missing_price_keys):
            errors.append(
                "Some sales item/store combinations have no price history "
                f"({len(missing_price_keys)} combinations)."
            )


def validate_raw_data(
    calendar: pd.DataFrame,
    sales: pd.DataFrame,
    prices: pd.DataFrame,
    *,
    expected_sales_days: int = EXPECTED_EVALUATION_DAYS,
    raise_on_error: bool = True,
) -> ValidationReport:
    """Validate schemas, values, uniqueness, and relationships in raw M5 data.

    Args:
        calendar: Contents of ``calendar.csv``.
        sales: Contents of ``sales_train_evaluation.csv``.
        prices: Contents of ``sell_prices.csv``.
        expected_sales_days: Required consecutive demand columns, starting at d_1.
        raise_on_error: Raise ``DataValidationError`` when errors are found.

    Returns:
        A report containing all validation errors and non-blocking warnings.

    Raises:
        ValueError: If ``expected_sales_days`` is not positive.
        DataValidationError: If validation fails and ``raise_on_error`` is true.
    """
    if expected_sales_days < 1:
        raise ValueError("expected_sales_days must be at least 1.")

    errors: list[str] = []
    warnings: list[str] = []
    _validate_calendar(calendar, errors, warnings)
    day_columns = _validate_sales(sales, expected_sales_days, errors, warnings)
    _validate_prices(prices, errors, warnings)
    _validate_relationships(calendar, sales, prices, day_columns, errors)

    report = ValidationReport(tuple(errors), tuple(warnings))
    if raise_on_error and not report.is_valid:
        raise DataValidationError(report)
    return report
