"""Leakage-safe feature engineering for item-store demand series."""

import numpy as np
import pandas as pd


SERIES_KEYS = ("store_id", "item_id")
LAG_DAYS = (1, 7, 14, 28)
ROLLING_MEAN_WINDOWS = (7, 14, 28)
ROLLING_STD_WINDOWS = (7, 28)
SALES_SUM_WINDOWS = (7, 28)
TARGET_HORIZON = 7

REQUIRED_INPUT_COLUMNS = {
    *SERIES_KEYS,
    "date",
    "demand",
    "sell_price",
    "month",
}
MODEL_FEATURE_COLUMNS = (
    "lag_1",
    "lag_7",
    "lag_14",
    "lag_28",
    "rolling_mean_7",
    "rolling_mean_14",
    "rolling_mean_28",
    "rolling_std_7",
    "rolling_std_28",
    "sales_sum_7",
    "sales_sum_28",
    "zero_rate_28",
    "target_7d",
)


def _future_sum(series: pd.Series, horizon: int) -> pd.Series:
    """Sum the next ``horizon`` values without allocating shifted columns."""
    return (
        series.iloc[::-1]
        .rolling(window=horizon, min_periods=horizon)
        .sum()
        .iloc[::-1]
        .shift(-1)
    )


def _past_zero_rate(series: pd.Series, window: int) -> pd.Series:
    """Calculate a prior-window zero rate while preserving the first missing row."""
    shifted = series.shift(1)
    zero_indicator = shifted.eq(0).astype("float32").where(shifted.notna())
    return zero_indicator.rolling(window=window, min_periods=window).mean()


def build_features(
    data: pd.DataFrame,
    *,
    drop_incomplete: bool = True,
    target_horizon: int = TARGET_HORIZON,
) -> pd.DataFrame:
    """Build leakage-safe model features for one or more stores.

    All history calculations are isolated by ``store_id`` and ``item_id``.
    Leading rows before a product's first known price are removed. Internal
    price gaps are filled only from earlier observations; future prices are
    never backfilled into the past.

    Args:
        data: A merged daily panel, normally returned by ``merge_store_data``.
        drop_incomplete: Remove rows without a full 28-day history or complete
            future target. Keep them when inspecting intermediate features.
        target_horizon: Number of future days summed into the target.

    Returns:
        A sorted feature DataFrame. With the default horizon the label is
        ``target_7d``.

    Raises:
        ValueError: If required data is invalid or a product has no usable price.
    """
    if target_horizon < 1:
        raise ValueError("target_horizon must be at least 1.")

    missing = sorted(REQUIRED_INPUT_COLUMNS.difference(data.columns))
    if missing:
        raise ValueError(
            "Feature input is missing columns: " + ", ".join(missing) + "."
        )
    if data.empty:
        raise ValueError("Feature input contains no rows.")

    frame = data.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    frame = frame.sort_values([*SERIES_KEYS, "date"], kind="stable").reset_index(
        drop=True
    )
    if frame.duplicated(subset=[*SERIES_KEYS, "date"]).any():
        raise ValueError("Feature input contains duplicate item-store dates.")
    if frame["demand"].isna().any() or (frame["demand"] < 0).any():
        raise ValueError("Demand must be present and non-negative.")

    grouping_values = [frame[column] for column in SERIES_KEYS]
    frame["release_date"] = (
        frame["date"]
        .where(frame["sell_price"].notna())
        .groupby(grouping_values, observed=True)
        .transform("min")
    )
    if frame["release_date"].isna().any():
        never_priced = frame.loc[
            frame["release_date"].isna(), list(SERIES_KEYS)
        ].drop_duplicates()
        raise ValueError(
            f"{len(never_priced):,} item-store series have no known selling price."
        )

    frame = frame.loc[frame["date"] >= frame["release_date"]].copy()
    frame["sell_price"] = frame.groupby(
        list(SERIES_KEYS), observed=True, sort=False
    )["sell_price"].ffill()
    if frame["sell_price"].isna().any():
        raise ValueError("A selling price is still missing after the release date.")
    if (frame["sell_price"] <= 0).any():
        raise ValueError("Selling prices must be positive after release.")

    frame["days_since_release"] = (
        frame["date"] - frame["release_date"]
    ).dt.days.astype("int16")
    frame["day_of_week"] = frame["date"].dt.dayofweek.astype("int8")
    frame["day_of_month"] = frame["date"].dt.day.astype("int8")
    frame["week_of_year"] = frame["date"].dt.isocalendar().week.astype("int16")
    frame["quarter"] = frame["date"].dt.quarter.astype("int8")
    frame["is_weekend"] = frame["day_of_week"].ge(5).astype("int8")

    event_columns = [
        column for column in ("event_name_1", "event_name_2") if column in frame
    ]
    if event_columns:
        event_mask = pd.Series(False, index=frame.index)
        for column in event_columns:
            event_mask |= frame[column].notna() & frame[column].ne("NoEvent")
        frame["is_event"] = event_mask.astype("int8")
    else:
        frame["is_event"] = np.int8(0)

    grouped_demand = frame.groupby(
        list(SERIES_KEYS), observed=True, sort=False
    )["demand"]
    for lag in LAG_DAYS:
        frame[f"lag_{lag}"] = grouped_demand.shift(lag).astype("float32")

    rolling_sums: dict[int, pd.Series] = {}
    for window in ROLLING_MEAN_WINDOWS:
        rolling_sum = grouped_demand.transform(
            lambda series, size=window: series.shift(1)
            .rolling(window=size, min_periods=size)
            .sum()
        ).astype("float32")
        rolling_sums[window] = rolling_sum
        frame[f"rolling_mean_{window}"] = rolling_sum.div(window).astype("float32")
    for window in ROLLING_STD_WINDOWS:
        frame[f"rolling_std_{window}"] = grouped_demand.transform(
            lambda series, size=window: series.shift(1)
            .rolling(window=size, min_periods=size)
            .std()
        ).astype("float32")
    for window in SALES_SUM_WINDOWS:
        frame[f"sales_sum_{window}"] = rolling_sums[window]
    frame["zero_rate_28"] = grouped_demand.transform(
        _past_zero_rate, window=28
    ).astype("float32")

    grouped_price = frame.groupby(
        list(SERIES_KEYS), observed=True, sort=False
    )["sell_price"]
    previous_price = grouped_price.shift(1)
    frame["price_change"] = (frame["sell_price"] - previous_price).fillna(0).astype(
        "float32"
    )
    frame["price_change_pct"] = (
        frame["price_change"].div(previous_price).replace([np.inf, -np.inf], np.nan)
    ).fillna(0).astype("float32")

    frame["dow_sin"] = np.sin(2 * np.pi * frame["day_of_week"] / 7).astype(
        "float32"
    )
    frame["dow_cos"] = np.cos(2 * np.pi * frame["day_of_week"] / 7).astype(
        "float32"
    )
    frame["month_sin"] = np.sin(2 * np.pi * frame["month"] / 12).astype(
        "float32"
    )
    frame["month_cos"] = np.cos(2 * np.pi * frame["month"] / 12).astype(
        "float32"
    )

    target_column = f"target_{target_horizon}d"
    frame[target_column] = grouped_demand.transform(
        _future_sum, horizon=target_horizon
    ).astype("float32")

    required_model_columns = [
        *(column for column in MODEL_FEATURE_COLUMNS if column != "target_7d"),
        target_column,
    ]
    if drop_incomplete:
        frame = frame.dropna(subset=required_model_columns).reset_index(drop=True)
        if frame.empty:
            raise ValueError(
                "No model rows remain; each series needs at least 36 post-release days."
            )

    validate_feature_frame(
        frame,
        required_columns=required_model_columns if drop_incomplete else (),
    )
    return frame


def validate_feature_frame(
    frame: pd.DataFrame,
    *,
    required_columns: tuple[str, ...] | list[str] = MODEL_FEATURE_COLUMNS,
) -> None:
    """Validate identifiers, ranges, uniqueness, and model-feature completeness."""
    missing = sorted({*SERIES_KEYS, "date", "demand", "sell_price"}.difference(frame))
    if missing:
        raise ValueError(
            "Feature output is missing columns: " + ", ".join(missing) + "."
        )
    if frame.empty:
        raise ValueError("Feature output contains no rows.")
    if frame.duplicated(subset=[*SERIES_KEYS, "date"]).any():
        raise ValueError("Feature output contains duplicate item-store dates.")
    missing_required = sorted(set(required_columns).difference(frame.columns))
    if missing_required:
        raise ValueError(
            "Feature output is missing model columns: "
            + ", ".join(missing_required)
            + "."
        )
    if required_columns and frame[list(required_columns)].isna().any(axis=None):
        raise ValueError("Feature output contains missing required model values.")
    if (frame["demand"] < 0).any() or (frame["sell_price"] <= 0).any():
        raise ValueError("Feature output contains invalid demand or price values.")
    target_columns = [column for column in frame if column.startswith("target_")]
    if target_columns and (frame[target_columns] < 0).any(axis=None):
        raise ValueError("Feature output contains a negative target.")
