"""FastAPI application for SmartStock AI."""

from fastapi import FastAPI

from api.schemas import HealthResponse


app = FastAPI(
    title="SmartStock AI API",
    description="API foundation for demand forecasting and inventory support.",
    version="0.1.0",
)


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health_check() -> HealthResponse:
    """Return the current API health status."""
    return HealthResponse(status="healthy", service="SmartStock AI")

