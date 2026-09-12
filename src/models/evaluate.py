"""Final held-out evaluation of an already selected forecasting bundle."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from src.models.artifacts import SavedForecaster


def error_totals(actual, predicted) -> dict:
    """Accumulate errors so overall metrics weight observations, not stores."""
    actual = np.asarray(actual, dtype=np.float64).reshape(-1)
    predicted = np.asarray(predicted, dtype=np.float64).reshape(-1)
    if actual.size == 0 or actual.shape != predicted.shape:
        raise ValueError("Actuals and predictions must have equal nonzero lengths.")
    if not np.isfinite(actual).all() or not np.isfinite(predicted).all():
        raise ValueError("Actuals and predictions must be finite.")
    error = actual - predicted
    return {
        "Rows": int(actual.size),
        "absolute_error": float(np.abs(error).sum()),
        "squared_error": float(np.square(error).sum()),
        "absolute_actual": float(np.abs(actual).sum()),
    }


def metrics_from_totals(totals: dict) -> dict:
    """Convert additive error totals into MAE, RMSE, and percentage WAPE."""
    return {
        "Rows": totals["Rows"],
        "MAE": totals["absolute_error"] / totals["Rows"],
        "RMSE": float(np.sqrt(totals["squared_error"] / totals["Rows"])),
        "WAPE": (
            totals["absolute_error"] / totals["absolute_actual"] * 100
            if totals["absolute_actual"] else np.nan
        ),
    }


def evaluate_model(
    bundle_dir: str | Path,
    *,
    features_dir: str | Path,
    output_dir: str | Path,
    store_ids: list[str] | tuple[str, ...],
    test_start: str = "2016-04-18",
    test_end: str = "2016-05-15",
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Evaluate all test rows without fitting or selecting another model."""
    bundle_dir = Path(bundle_dir).resolve()
    features_dir = Path(features_dir).resolve()
    output_dir = Path(output_dir).resolve()
    metadata_path = bundle_dir / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    start, end = pd.Timestamp(test_start), pd.Timestamp(test_end)
    if start > end:
        raise ValueError("Test start must be on or before test end.")
    label_end = pd.Timestamp(metadata["validation_end"]) + pd.Timedelta(
        days=metadata["forecast_horizon_days"]
    )
    if start <= label_end:
        raise ValueError("Test origins must follow validation labels and the purge gap.")
    if not store_ids or len(set(store_ids)) != len(store_ids):
        raise ValueError("Provide a nonempty list of unique stores.")
    paths = {
        store: features_dir / f"store_id={store}" / "features.parquet"
        for store in store_ids
    }
    for path in paths.values():
        if not path.is_file():
            raise FileNotFoundError(path)

    artifact_paths = [bundle_dir / "preprocessing.joblib"]
    if metadata["input_kind"] != "seasonal_naive":
        artifact_paths.append(bundle_dir / "model.keras")
    hashes = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in artifact_paths
    }
    forecaster = SavedForecaster(bundle_dir)
    preprocessing = forecaster.preprocessing
    target = preprocessing["target"]
    columns = list(dict.fromkeys(
        ["date", "item_id", "store_id", target, "sales_sum_7"]
        + preprocessing["numerical_features"]
        + preprocessing["categorical_features"]
    ))
    prediction_dir = output_dir / "predictions"
    prediction_dir.mkdir(parents=True, exist_ok=True)
    expected_dates = pd.date_range(start, end)
    totals_by_model = {}
    store_results = []

    for store, path in paths.items():
        frame = pd.read_parquet(
            path, columns=columns,
            filters=[("date", ">=", start), ("date", "<=", end)],
        )
        dates = pd.DatetimeIndex(pd.to_datetime(frame["date"]).unique()).sort_values()
        if not dates.equals(expected_dates):
            raise ValueError(f"{store}: incomplete test-date coverage.")
        if set(frame["store_id"].astype(str)) != {store}:
            raise ValueError(f"{store}: unexpected store IDs in the partition.")
        if frame.duplicated(["store_id", "item_id", "date"]).any():
            raise ValueError(f"{store}: duplicate item-store forecast origins.")
        actual = frame[target].to_numpy(dtype=np.float64)
        if (actual < 0).any():
            raise ValueError(f"{store}: negative demand targets.")
        predictions = {
            "Seasonal Naive": frame["sales_sum_7"].to_numpy(dtype=np.float64),
            "Selected model": forecaster.predict(frame),
        }
        for name, predicted in predictions.items():
            totals = error_totals(actual, predicted)
            aggregate = totals_by_model.setdefault(name, dict.fromkeys(totals, 0))
            for key, value in totals.items():
                aggregate[key] += value
            store_results.append({
                "store_id": store, "Model": name, **metrics_from_totals(totals),
            })
        saved_predictions = frame[["date", "item_id", "store_id", target]].copy()
        saved_predictions["naive_prediction"] = predictions["Seasonal Naive"]
        saved_predictions["model_prediction"] = predictions["Selected model"]
        saved_predictions.to_parquet(prediction_dir / f"{store}.parquet", index=False)
        print(f"Evaluated {store}: {len(frame):,} test rows", flush=True)

    summary = pd.DataFrame([
        {"Model": name, **metrics_from_totals(totals)}
        for name, totals in totals_by_model.items()
    ])
    baseline_wape = summary.loc[summary["Model"] == "Seasonal Naive", "WAPE"].iloc[0]
    summary["WAPE reduction vs naive (%)"] = (
        (baseline_wape - summary["WAPE"]) / baseline_wape * 100
        if np.isfinite(baseline_wape) and baseline_wape > 0 else np.nan
    )
    summary["Model"] = summary["Model"].replace(
        {"Selected model": metadata["model_name"]}
    )
    by_store = pd.DataFrame(store_results)
    by_store["Model"] = by_store["Model"].replace(
        {"Selected model": metadata["model_name"]}
    )
    for path in artifact_paths:
        if hashlib.sha256(path.read_bytes()).hexdigest() != hashes[path.name]:
            raise RuntimeError("Model or preprocessing changed during evaluation.")
    model_metrics = metrics_from_totals(totals_by_model["Selected model"])
    evaluation = {
        "model_name": metadata["model_name"],
        "bundle_dir": str(bundle_dir),
        "artifact_sha256": hashes,
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "test_start": str(start.date()),
        "test_end": str(end.date()),
        "forecast_origin_days": len(expected_dates),
        "forecast_horizon_days": metadata["forecast_horizon_days"],
        "stores": list(store_ids),
        "test_rows": model_metrics["Rows"],
        "sampled": False,
        "refitted": False,
        "model_metrics": model_metrics,
        "naive_metrics": metrics_from_totals(totals_by_model["Seasonal Naive"]),
        "protocol": "Rolling forecast origins using observed history at each origin.",
    }
    summary.to_csv(output_dir / "test_summary.csv", index=False)
    by_store.to_csv(output_dir / "test_by_store.csv", index=False)
    (output_dir / "evaluation.json").write_text(
        json.dumps(evaluation, indent=2) + "\n", encoding="utf-8"
    )
    metadata.update(test_evaluated=True, test_evaluation=evaluation)
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return summary, by_store, evaluation
