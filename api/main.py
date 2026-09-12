"""FastAPI application for SmartStock AI."""

from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException, status

from api.inventory_service import calculate_inventory_recommendation
from api.predictor import DemandPredictor
from api.schemas import HealthResponse, PredictionRequest, PredictionResponse


app = FastAPI(
    title="SmartStock AI API",
    description="Seven-day demand forecasting and inventory recommendations.",
    version="0.1.0",
)


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health_check() -> HealthResponse:
    """Return the current API health status."""
    return HealthResponse(status="healthy", service="SmartStock AI")


@lru_cache(maxsize=1)
def get_predictor() -> DemandPredictor:
    """Load and cache the frozen model bundle on the first prediction request."""
    try:
        return DemandPredictor()
    except (FileNotFoundError, OSError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Prediction model is unavailable: {error}",
        ) from error


@app.post("/predict", response_model=PredictionResponse, tags=["forecasting"])
def predict_demand(
    request: PredictionRequest,
    predictor: DemandPredictor = Depends(get_predictor),
) -> PredictionResponse:
    """Forecast demand and return the corresponding inventory recommendation."""
    feature_row = request.features.model_dump()
    feature_row["item_id"] = request.product
    try:
        predicted_demand = predictor.predict(feature_row)
        recommendation = calculate_inventory_recommendation(
            predicted_demand=predicted_demand,
            current_stock=request.current_stock,
            safety_stock=request.safety_stock,
        )
    except (ValueError, RuntimeError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    return PredictionResponse(product=request.product, **recommendation)
