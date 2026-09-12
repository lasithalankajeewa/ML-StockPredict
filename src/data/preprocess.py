"""Memory-conscious preprocessing utilities for SmartStock AI."""

from collections.abc import Mapping

import pandas as pd
from pandas.api.types import is_numeric_dtype

from src.config import DEVELOPMENT_STORE_ID
from src.data.validation import DAY_COLUMN_PATTERN, SALES_ID_COLUMNS


REQUIRED_DATASETS = {"calendar", "sales", "prices"}

CALENDAR_COLUMNS = (
    "d",
    "date",
    "wm_yr_wk",
    "weekday",
    "wday",
    "month",
    "year",
    "event_name_1",
    "event_type_1",
    "event_name_2",
    "event_type_2",
    "snap_CA",
    "snap_TX",
    "snap_WI",
)
PRICE_KEYS = ("store_id", "item_id", "wm_yr_wk")


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


def merge_store_data(
    data: Mapping[str, pd.DataFrame],
    store_id: str = DEVELOPMENT_STORE_ID,
) -> pd.DataFrame:
    """Create a cleaned daily panel for one store.

    Working store by store prevents the roughly 59 million-row all-store panel
    from being materialized in memory. The returned frame is ready for
    :func:`src.data.features.build_features`.

    Args:
        data: Validated raw M5 calendar, sales, and price tables.
        store_id: Store partition to prepare.

    Returns:
        Daily item-store demand merged with calendar and weekly price data.

    Raises:
        ValueError: If a merge key is missing or duplicated, a merge changes the
            row count, or the store cannot be mapped to a SNAP column.
    """
    store_data = select_store_subset(data, store_id=store_id)
    sales_long = reshape_sales_to_long(store_data["sales"])

    calendar = store_data["calendar"]
    missing_calendar = sorted(set(CALENDAR_COLUMNS).difference(calendar.columns))
    if missing_calendar:
        raise ValueError(
            "The calendar dataset is missing columns: "
            + ", ".join(missing_calendar)
            + "."
        )
    if calendar.duplicated(subset=["d"]).any():
        raise ValueError("The calendar dataset contains duplicate d values.")

    calendar = calendar.loc[:, CALENDAR_COLUMNS].copy()
    sales_days = sales_long["d"].cat.categories
    calendar = calendar.loc[calendar["d"].isin(sales_days)].copy()
    missing_days = sales_days.difference(calendar["d"])
    if not missing_days.empty:
        preview = ", ".join(map(str, missing_days[:5]))
        raise ValueError(f"Calendar data is missing sales days: {preview}.")
    calendar["date"] = pd.to_datetime(calendar["date"], errors="raise")
    calendar["d"] = pd.Categorical(
        calendar["d"], categories=sales_days, ordered=True
    )

    expected_rows = len(sales_long)
    merged = sales_long.merge(
        calendar,
        on="d",
        how="left",
        validate="many_to_one",
        sort=False,
    )
    if len(merged) != expected_rows or merged["date"].isna().any():
        raise ValueError("The calendar merge did not preserve every sales row.")

    prices = store_data["prices"]
    missing_price_columns = sorted(
        set((*PRICE_KEYS, "sell_price")).difference(prices.columns)
    )
    if missing_price_columns:
        raise ValueError(
            "The price dataset is missing columns: "
            + ", ".join(missing_price_columns)
            + "."
        )
    if prices.duplicated(subset=list(PRICE_KEYS)).any():
        raise ValueError("The price dataset contains duplicate item-week keys.")

    prices = prices.loc[:, [*PRICE_KEYS, "sell_price"]].copy()
    for column in ("store_id", "item_id"):
        prices[column] = pd.Categorical(
            prices[column], categories=merged[column].cat.categories
        )
    prices["sell_price"] = pd.to_numeric(
        prices["sell_price"], downcast="float"
    )

    merged = merged.merge(
        prices,
        on=list(PRICE_KEYS),
        how="left",
        validate="many_to_one",
        sort=False,
    )
    if len(merged) != expected_rows:
        raise ValueError("The price merge did not preserve every sales row.")

    state_ids = merged["state_id"].dropna().astype("string").unique()
    if len(state_ids) != 1:
        raise ValueError(f"Store {store_id!r} does not map to exactly one state.")
    snap_column = f"snap_{state_ids[0]}"
    if snap_column not in merged.columns:
        raise ValueError(f"Calendar data is missing {snap_column!r}.")
    merged["snap"] = pd.to_numeric(merged[snap_column], downcast="unsigned")
    merged = merged.drop(columns=["snap_CA", "snap_TX", "snap_WI"])

    event_columns = (
        "event_name_1",
        "event_type_1",
        "event_name_2",
        "event_type_2",
    )
    for column in event_columns:
        merged[column] = merged[column].fillna("NoEvent").astype("category")

    for column in ("weekday",):
        merged[column] = merged[column].astype("category")
    for column in ("wday", "month"):
        merged[column] = pd.to_numeric(merged[column], downcast="unsigned")
    merged["year"] = pd.to_numeric(merged["year"], downcast="unsigned")
    merged["wm_yr_wk"] = pd.to_numeric(
        merged["wm_yr_wk"], downcast="unsigned"
    )

    return merged.sort_values(
        ["store_id", "item_id", "date"], kind="stable"
    ).reset_index(drop=True)
