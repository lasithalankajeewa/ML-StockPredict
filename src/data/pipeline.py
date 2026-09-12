"""Build memory-bounded, per-store feature partitions from raw M5 data."""

from __future__ import annotations

import argparse
import gc
from pathlib import Path

import pandas as pd

from src.config import FEATURES_DATA_DIR
from src.data.features import build_features, validate_feature_frame
from src.data.load_data import load_raw_data
from src.data.preprocess import merge_store_data


def discover_store_ids(sales: pd.DataFrame) -> list[str]:
    """Return sorted, non-empty store identifiers from the sales table."""
    if "store_id" not in sales:
        raise ValueError("The sales dataset is missing the store_id column.")
    stores = sorted(sales["store_id"].dropna().astype("string").unique().tolist())
    if not stores:
        raise ValueError("The sales dataset contains no store identifiers.")
    return stores


def build_feature_partitions(
    raw_data: dict[str, pd.DataFrame],
    *,
    store_ids: list[str] | tuple[str, ...] | None = None,
    output_dir: Path = FEATURES_DATA_DIR,
    overwrite: bool = False,
) -> pd.DataFrame:
    """Build and save one model-ready Parquet file at a time per store.

    Existing files are protected unless ``overwrite=True``. A manifest is saved
    after all requested stores complete successfully.
    """
    available_stores = discover_store_ids(raw_data["sales"])
    requested_stores = available_stores if store_ids is None else list(store_ids)
    unknown = sorted(set(requested_stores).difference(available_stores))
    if unknown:
        raise ValueError("Unknown stores requested: " + ", ".join(unknown) + ".")
    if not requested_stores:
        raise ValueError("At least one store must be requested.")
    if len(requested_stores) != len(set(requested_stores)):
        raise ValueError("Store identifiers must not be repeated.")

    targets = {
        store_id: output_dir / f"store_id={store_id}" / "features.parquet"
        for store_id in requested_stores
    }
    existing = [str(path) for path in targets.values() if path.exists()]
    if existing and not overwrite:
        raise FileExistsError(
            "Feature partitions already exist; use --overwrite to replace them: "
            + ", ".join(existing)
        )

    results: list[dict[str, object]] = []
    for store_id in requested_stores:
        print(f"[{store_id}] merging raw data...")
        merged = merge_store_data(raw_data, store_id=store_id)
        input_rows = len(merged)

        print(f"[{store_id}] building leakage-safe features...")
        features = build_features(merged)
        del merged
        gc.collect()

        validate_feature_frame(features)
        if features["store_id"].astype("string").nunique() != 1:
            raise ValueError(f"Partition {store_id!r} contains more than one store.")
        actual_store = str(features["store_id"].astype("string").iloc[0])
        if actual_store != store_id:
            raise ValueError(
                f"Partition {store_id!r} unexpectedly contains {actual_store!r}."
            )

        target = targets[store_id]
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name("features.tmp.parquet")
        try:
            features.to_parquet(temporary, index=False, engine="pyarrow")
            temporary.replace(target)
        finally:
            if temporary.exists():
                temporary.unlink()

        result = {
            "store_id": store_id,
            "input_rows": input_rows,
            "feature_rows": len(features),
            "start_date": features["date"].min(),
            "end_date": features["date"].max(),
            "file_size_mb": round(target.stat().st_size / 1024**2, 2),
            "path": str(target),
        }
        results.append(result)
        print(
            f"[{store_id}] saved {len(features):,} rows "
            f"to {target} ({result['file_size_mb']} MB)."
        )
        del features
        gc.collect()

    manifest = pd.DataFrame(results)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(output_dir / "manifest.csv", index=False)
    return manifest


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build M5 feature Parquet files one store at a time."
    )
    parser.add_argument(
        "--stores",
        nargs="+",
        help="Store IDs to build (for example CA_1 TX_1). Omit for all stores.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=FEATURES_DATA_DIR,
        help=f"Partition root (default: {FEATURES_DATA_DIR}).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace feature files that already exist.",
    )
    return parser.parse_args()


def main() -> None:
    """Command-line entry point."""
    args = _parse_args()
    raw_data = load_raw_data(validate=True)
    manifest = build_feature_partitions(
        raw_data,
        store_ids=args.stores,
        output_dir=args.output_dir,
        overwrite=args.overwrite,
    )
    print("\nCompleted feature partitions:")
    print(manifest.to_string(index=False))


if __name__ == "__main__":
    main()
