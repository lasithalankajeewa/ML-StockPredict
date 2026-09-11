"""Memory-conscious preprocessing utilities for SmartStock AI."""

from collections.abc import Mapping

import pandas as pd
from pandas.api.types import is_numeric_dtype

from src.config import DEVELOPMENT_STORE_ID
from src.data.validation import DAY_COLUMN_PATTERN, SALES_ID_COLUMNS


REQUIRED_DATASETS = {"calendar", "sales", "prices"}


def select_store_subset(
    data: Mapping[str, pd.DataFrame],
    store_id: str = DEVELOPMENT_STORE_ID,
) -> dict[str, pd.DataFrame]:
    """Select one store before memory-intensive transformations.

    The sales and price tables are filtered to the requested store. The calendar
    table is retained in full because it is shared by all stores and is small.

    Args:
        data: Mapping containing validated ``calendar``, ``sales``, and ``prices``
            DataFrames, such as the result returned by ``load_raw_data``.
        store_id: Store identifier to retain.

    Returns:
        A new mapping with the complete calendar and copied, index-reset sales and
        price subsets for the selected store.

    Raises:
        ValueError: If the store identifier is blank, required datasets or columns
            are missing, or the store has no sales or price records.
    """
    if not store_id.strip():
        raise ValueError("store_id must not be blank.")

    missing_datasets = sorted(REQUIRED_DATASETS.difference(data))
    if missing_datasets:
        raise ValueError(
            "Missing required datasets: " + ", ".join(missing_datasets) + "."
        )

    sales = data["sales"]
    prices = data["prices"]
    if "store_id" not in sales.columns:
        raise ValueError("The sales dataset is missing the store_id column.")
    if "store_id" not in prices.columns:
        raise ValueError("The prices dataset is missing the store_id column.")

    available_stores = sorted(sales["store_id"].dropna().astype(str).unique())
    if store_id not in available_stores:
        available = ", ".join(available_stores) or "none"
        raise ValueError(
            f"Store {store_id!r} was not found in sales data. "
            f"Available stores: {available}."
        )

    store_sales = sales.loc[sales["store_id"] == store_id].copy()
    store_prices = prices.loc[prices["store_id"] == store_id].copy()
    if store_prices.empty:
        raise ValueError(f"Store {store_id!r} has no selling-price records.")

    return {
        "calendar": data["calendar"],
        "sales": store_sales.reset_index(drop=True),
        "prices": store_prices.reset_index(drop=True),
    }


def reshape_sales_to_long(sales: pd.DataFrame) -> pd.DataFrame:
    """Convert an M5 sales subset from wide daily columns to long format.

    Identifier and day columns are stored as categoricals, and non-negative demand
    is downcast to the smallest unsigned integer type that can represent it. These
    conversions substantially reduce the memory used by the resulting table.

    Args:
        sales: A validated M5 sales DataFrame, preferably filtered to one store.

    Returns:
        A DataFrame with identifier columns followed by ``d`` and ``demand``.
        Rows are ordered by day and retain the input product order within each day.

    Raises:
        ValueError: If identifiers or daily demand columns are missing, column
            names are duplicated, or demand contains non-numeric, missing, or
            negative values.
    """
    if sales.empty:
        raise ValueError("The sales dataset contains no rows.")
    if sales.columns.duplicated().any():
        raise ValueError("The sales dataset contains duplicate column names.")

    missing_identifiers = sorted(SALES_ID_COLUMNS.difference(sales.columns))
    if missing_identifiers:
        raise ValueError(
            "The sales dataset is missing identifier columns: "
            + ", ".join(missing_identifiers)
            + "."
        )

    day_columns_with_numbers = []
    for column in sales.columns:
        match = DAY_COLUMN_PATTERN.fullmatch(str(column))
        if match:
            day_columns_with_numbers.append((int(match.group(1)), column))
    if not day_columns_with_numbers:
        raise ValueError("The sales dataset contains no d_<number> demand columns.")

    day_columns_with_numbers.sort(key=lambda value: value[0])
    day_numbers = [number for number, _ in day_columns_with_numbers]
    if len(day_numbers) != len(set(day_numbers)):
        raise ValueError("The sales dataset contains duplicate demand day numbers.")

    day_columns = [column for _, column in day_columns_with_numbers]
    non_numeric = [
        column for column in day_columns if not is_numeric_dtype(sales[column])
    ]
    if non_numeric:
        preview = ", ".join(map(str, non_numeric[:5]))
        raise ValueError(f"Demand columns must be numeric; invalid: {preview}.")

    demand_values = sales[day_columns]
    if demand_values.isna().any(axis=None):
        raise ValueError("Demand columns contain missing values.")
    if (demand_values < 0).any(axis=None):
        raise ValueError("Demand values cannot be negative.")

    identifier_columns = [
        column for column in sales.columns if column in SALES_ID_COLUMNS
    ]
    sales_long = sales.melt(
        id_vars=identifier_columns,
        value_vars=day_columns,
        var_name="d",
        value_name="demand",
        ignore_index=True,
    )

    for column in identifier_columns:
        sales_long[column] = sales_long[column].astype("category")
    sales_long["d"] = pd.Categorical(
        sales_long["d"], categories=day_columns, ordered=True
    )
    sales_long["demand"] = pd.to_numeric(
        sales_long["demand"], downcast="unsigned"
    )

    return sales_long
