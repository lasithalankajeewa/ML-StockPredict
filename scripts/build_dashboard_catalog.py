"""Build the compact product catalog consumed by the Next.js dashboard."""

import json
import math
import zlib
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PREDICTIONS_DIR = PROJECT_ROOT / "reports" / "results" / "final_test" / "predictions"
FEATURES_DIR = PROJECT_ROOT / "data" / "processed" / "features"
OUTPUT_PATH = PROJECT_ROOT / "frontend" / "data" / "products.json"
FORECAST_DATE = pd.Timestamp("2016-05-15")
HISTORY_START = FORECAST_DATE - pd.Timedelta(days=13)


def inventory_values(store_id: str, item_id: str, forecast: int) -> tuple[int, int]:
    """Create stable demonstration inventory because M5 has no stock levels."""
    ratios = (0.55, 0.82, 1.0, 1.12, 1.35)
    bucket = zlib.crc32(f"{store_id}:{item_id}".encode()) % len(ratios)
    current_stock = round(forecast * ratios[bucket])
    safety_stock = max(1, math.ceil(forecast * 0.15))
    return current_stock, safety_stock


def build_catalog() -> list[dict]:
    """Combine the final DNN forecast with real fourteen-day demand history."""
    catalog = []
    for prediction_path in sorted(PREDICTIONS_DIR.glob("*.parquet")):
        store_id = prediction_path.stem
        predictions = pd.read_parquet(
            prediction_path,
            filters=[("date", "==", FORECAST_DATE)],
        )
        history = pd.read_parquet(
            FEATURES_DIR / f"store_id={store_id}" / "features.parquet",
            columns=["date", "item_id", "cat_id", "demand"],
            filters=[
                ("date", ">=", HISTORY_START),
                ("date", "<=", FORECAST_DATE),
            ],
        )
        history["item_id"] = history["item_id"].astype(str)
        predictions["item_id"] = predictions["item_id"].astype(str)
        history = history.sort_values(["item_id", "date"])
        demand_history = history.groupby("item_id", observed=True)["demand"].agg(list)
        categories = history.groupby("item_id", observed=True)["cat_id"].first()

        for row in predictions.itertuples(index=False):
            forecast = max(0, math.ceil(float(row.model_prediction)))
            current_stock, safety_stock = inventory_values(
                store_id, row.item_id, forecast
            )
            reorder = max(0, forecast + safety_stock - current_stock)
            if current_stock < forecast:
                risk = "High"
            elif current_stock < forecast + safety_stock:
                risk = "Watch"
            else:
                risk = "Healthy"
            values = demand_history[row.item_id]
            if len(values) != 14:
                raise ValueError(
                    f"{store_id}/{row.item_id} has {len(values)} history rows, expected 14."
                )
            category = str(categories[row.item_id]).title()
            catalog.append(
                {
                    "id": row.item_id,
                    "category": category,
                    "store": store_id,
                    "currentStock": current_stock,
                    "safetyStock": safety_stock,
                    "forecast": forecast,
                    "reorder": reorder,
                    "risk": risk,
                    "history": [int(value) for value in values],
                }
            )
        print(f"Added {store_id}: {len(predictions):,} products")
    return catalog


def main() -> None:
    catalog = build_catalog()
    expected_rows = 3_049 * 10
    if len(catalog) != expected_rows:
        raise ValueError(f"Expected {expected_rows:,} catalog rows, found {len(catalog):,}.")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(catalog, separators=(",", ":")), encoding="utf-8"
    )
    print(f"Saved {len(catalog):,} product-store rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
