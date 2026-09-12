"""Tests for demand prediction and inventory recommendation endpoints."""

from fastapi.testclient import TestClient

from api.inventory_service import calculate_inventory_recommendation
from api.main import app, get_predictor


class StubPredictor:
    """Avoid loading TensorFlow while testing the HTTP contract."""

    def predict(self, features):
        assert features["item_id"] == "FOODS_1_001"
        assert features["store_id"] == "CA_1"
        return 36.2


def feature_payload():
    return {
        "lag_1": 4,
        "lag_7": 5,
        "lag_14": 3,
        "lag_28": 4,
        "rolling_mean_7": 4.2,
        "rolling_mean_14": 4.0,
        "rolling_mean_28": 3.8,
        "rolling_std_7": 1.1,
        "rolling_std_28": 1.4,
        "sales_sum_7": 29,
        "sales_sum_28": 106,
        "zero_rate_28": 0.1,
        "sell_price": 2.5,
        "price_change": 0,
        "price_change_pct": 0,
        "days_since_release": 400,
        "day_of_week": 2,
        "month": 5,
        "is_weekend": 0,
        "is_event": 0,
        "dow_sin": 0.9749,
        "dow_cos": -0.2225,
        "month_sin": 0.5,
        "month_cos": -0.866,
        "dept_id": "FOODS_1",
        "cat_id": "FOODS",
        "store_id": "CA_1",
        "state_id": "CA",
    }


def test_predict_endpoint_returns_inventory_action():
    app.dependency_overrides[get_predictor] = lambda: StubPredictor()
    try:
        with TestClient(app) as client:
            response = client.post(
                "/predict",
                json={
                    "product": "FOODS_1_001",
                    "currentStock": 12,
                    "safetyStock": 6,
                    "features": feature_payload(),
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "product": "FOODS_1_001",
        "predictedDemand7Days": 37,
        "currentStock": 12,
        "safetyStock": 6,
        "recommendedReorder": 31,
        "riskLevel": "HIGH",
    }


def test_predict_endpoint_rejects_missing_model_feature():
    payload = feature_payload()
    payload.pop("lag_28")
    app.dependency_overrides[get_predictor] = lambda: StubPredictor()
    try:
        with TestClient(app) as client:
            response = client.post(
                "/predict",
                json={
                    "product": "FOODS_1_001",
                    "currentStock": 12,
                    "safetyStock": 6,
                    "features": payload,
                },
            )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 422


def test_inventory_risk_levels_and_nonnegative_reorder():
    high = calculate_inventory_recommendation(36.2, 12, 6)
    medium = calculate_inventory_recommendation(36.2, 40, 6)
    low = calculate_inventory_recommendation(36.2, 43, 6)
    assert (high["risk_level"], high["recommended_reorder"]) == ("HIGH", 31)
    assert (medium["risk_level"], medium["recommended_reorder"]) == ("MEDIUM", 3)
    assert (low["risk_level"], low["recommended_reorder"]) == ("LOW", 0)
