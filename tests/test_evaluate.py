"""Tests for held-out evaluation arithmetic and split protection."""

import json

import numpy as np
import pandas as pd
import pytest

from src.models.evaluate import error_totals, evaluate_model, metrics_from_totals


def test_overall_metrics_pool_rows_instead_of_averaging_stores():
    first = error_totals([10], [0])
    second = error_totals([10, 10, 10], [9, 9, 9])
    combined = {key: first[key] + second[key] for key in first}
    result = metrics_from_totals(combined)
    assert result["Rows"] == 4
    assert result["MAE"] == 3.25
    assert result["RMSE"] == pytest.approx(np.sqrt(103 / 4))
    assert result["WAPE"] == 32.5


def test_zero_actual_total_has_undefined_wape():
    result = metrics_from_totals(error_totals([0, 0], [1, 2]))
    assert result["MAE"] == 1.5
    assert np.isnan(result["WAPE"])


@pytest.mark.parametrize("actual,predicted", [([], []), ([1], [1, 2]), ([1], [np.nan])])
def test_invalid_metric_inputs_are_rejected(actual, predicted):
    with pytest.raises(ValueError):
        error_totals(actual, predicted)


def test_test_period_cannot_overlap_validation_labels(tmp_path):
    (tmp_path / "metadata.json").write_text(json.dumps({
        "validation_end": "2016-04-10", "forecast_horizon_days": 7,
    }))
    with pytest.raises(ValueError, match="purge gap"):
        evaluate_model(
            tmp_path, features_dir=tmp_path, output_dir=tmp_path / "results",
            store_ids=["CA_1"], test_start="2016-04-17", test_end="2016-05-15",
        )


def test_evaluation_saves_all_test_rows_and_metadata(tmp_path, monkeypatch):
    metadata = {
        "validation_end": "2016-04-10", "forecast_horizon_days": 7,
        "input_kind": "mixed", "model_name": "DNN (original)",
    }
    (tmp_path / "metadata.json").write_text(json.dumps(metadata))
    (tmp_path / "model.keras").write_bytes(b"unchanged model")
    (tmp_path / "preprocessing.joblib").write_bytes(b"unchanged transforms")

    class FrozenForecaster:
        def __init__(self, bundle):
            self.preprocessing = {
                "target": "target_7d", "numerical_features": ["sales_sum_7"],
                "categorical_features": [],
            }

        def predict(self, features):
            return features["sales_sum_7"].to_numpy() + 1

    monkeypatch.setattr("src.models.evaluate.SavedForecaster", FrozenForecaster)
    for store, baseline in [("CA_1", 5), ("CA_2", 8)]:
        path = tmp_path / f"store_id={store}"
        path.mkdir()
        pd.DataFrame({
            "date": pd.to_datetime(["2016-04-17", "2016-04-18", "2016-04-19"]),
            "item_id": ["item"] * 3, "store_id": [store] * 3,
            "target_7d": [999, 10, 10], "sales_sum_7": [0, baseline, baseline],
        }).to_parquet(path / "features.parquet", index=False)
    output = tmp_path / "results"
    summary, by_store, report = evaluate_model(
        tmp_path, features_dir=tmp_path, output_dir=output,
        store_ids=["CA_1", "CA_2"], test_start="2016-04-18", test_end="2016-04-19",
    )
    assert summary["Rows"].tolist() == [4, 4]
    assert summary["MAE"].tolist() == [3.5, 2.5]
    assert len(by_store) == 4
    assert report["test_rows"] == 4
    assert not report["refitted"]
    assert json.loads((tmp_path / "metadata.json").read_text())["test_evaluated"]
    assert (output / "test_summary.csv").is_file()
    for store in ["CA_1", "CA_2"]:
        assert len(pd.read_parquet(output / "predictions" / f"{store}.parquet")) == 2
