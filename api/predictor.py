"""Thin inference wrapper around the frozen forecasting bundle."""

from collections.abc import Mapping
import os
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv

from src.config import MODEL_DIR, PROJECT_ROOT
from src.models.artifacts import SavedForecaster


def resolve_model_bundle() -> Path:
    """Use an explicit bundle or the latest locally saved best-model bundle."""
    load_dotenv(PROJECT_ROOT / ".env")
    configured = os.getenv("SMARTSTOCK_MODEL_BUNDLE", "").strip()
    if configured:
        bundle = Path(configured).expanduser().resolve()
        if not bundle.is_dir():
            raise FileNotFoundError(
                f"SMARTSTOCK_MODEL_BUNDLE does not exist: {bundle}"
            )
        return bundle

    candidates = sorted((MODEL_DIR / "trained").glob("best_model_*"))
    if not candidates:
        raise FileNotFoundError(
            "No saved best-model bundle found under models/trained. "
            "Set SMARTSTOCK_MODEL_BUNDLE to the exported bundle directory."
        )
    return candidates[-1]


class DemandPredictor:
    """Load preprocessing and DNN artifacts once and predict one feature row."""

    def __init__(self, bundle_dir: str | Path | None = None) -> None:
        self.bundle_dir = (
            Path(bundle_dir).resolve()
            if bundle_dir is not None
            else resolve_model_bundle()
        )
        self.forecaster = SavedForecaster(self.bundle_dir)

    def predict(self, features: Mapping[str, Any]) -> float:
        """Return the raw next-seven-day demand prediction for one row."""
        predictions = self.forecaster.predict(pd.DataFrame([dict(features)]))
        if predictions.size != 1:
            raise RuntimeError("Expected exactly one prediction from the DNN.")
        return float(predictions[0])
