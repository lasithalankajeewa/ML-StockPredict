"""Load a saved forecasting model and its fitted feature preprocessing."""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


class SavedForecaster:
    """Predict seven-day demand from rows produced by the feature pipeline."""

    def __init__(self, bundle_dir: str | Path) -> None:
        bundle_dir = Path(bundle_dir)
        self.metadata = json.loads(
            (bundle_dir / "metadata.json").read_text(encoding="utf-8")
        )
        self.preprocessing = joblib.load(bundle_dir / "preprocessing.joblib")
        self.input_kind = self.metadata["input_kind"]
        if self.input_kind not in {"numerical", "mixed", "seasonal_naive"}:
            raise ValueError(f"Unknown model input kind: {self.input_kind}")
        self.model = None
        if self.input_kind != "seasonal_naive":
            from tensorflow import keras

            self.model = keras.models.load_model(
                bundle_dir / "model.keras", compile=False
            )

    def predict(self, features: pd.DataFrame, batch_size: int = 4096) -> np.ndarray:
        """Apply the saved transforms; never fit preprocessing on new data."""
        numerical = self.preprocessing["numerical_features"]
        categorical = self.preprocessing["categorical_features"]
        required = (
            ["sales_sum_7"] if self.input_kind == "seasonal_naive" else numerical
        )
        if self.input_kind == "mixed":
            required = required + categorical
        missing = sorted(set(required) - set(features.columns))
        if missing:
            raise ValueError(f"Missing required feature columns: {missing}")
        if features.empty:
            return np.empty(0, dtype=np.float32)

        if self.input_kind == "seasonal_naive":
            predictions = features["sales_sum_7"].to_numpy(dtype=np.float32)
        else:
            values = features[numerical].replace([np.inf, -np.inf], np.nan)
            values = self.preprocessing["num_imputer"].transform(values)
            values = self.preprocessing["scaler"].transform(values).astype("float32")
            model_inputs = values
            if self.input_kind == "mixed":
                model_inputs = {"numerical": values}
                for column in categorical:
                    # Zero is the same unknown-category index used in training.
                    model_inputs[column] = (
                        features[column]
                        .astype(str)
                        .map(self.preprocessing["category_maps"][column])
                        .fillna(0)
                        .to_numpy(dtype=np.int32)
                        .reshape(-1, 1)
                    )
            predictions = self.model.predict(
                model_inputs, batch_size=batch_size, verbose=0
            ).reshape(-1)

        if not np.isfinite(predictions).all():
            raise ValueError("Model produced non-finite predictions.")
        return predictions
