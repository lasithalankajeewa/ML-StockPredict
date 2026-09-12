"""Pydantic request and response schemas for the API."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat


class HealthResponse(BaseModel):
    """Response returned by the health-check endpoint."""

    status: str
    service: str


NonNegativeFloat = Annotated[FiniteFloat, Field(ge=0)]


class FeatureData(BaseModel):
    """One engineered feature row expected by the saved DNN."""

    model_config = ConfigDict(extra="forbid")

    lag_1: NonNegativeFloat
    lag_7: NonNegativeFloat
    lag_14: NonNegativeFloat
    lag_28: NonNegativeFloat
    rolling_mean_7: NonNegativeFloat
    rolling_mean_14: NonNegativeFloat
    rolling_mean_28: NonNegativeFloat
    rolling_std_7: NonNegativeFloat
    rolling_std_28: NonNegativeFloat
    sales_sum_7: NonNegativeFloat
    sales_sum_28: NonNegativeFloat
    zero_rate_28: Annotated[FiniteFloat, Field(ge=0, le=1)]
    sell_price: Annotated[FiniteFloat, Field(gt=0)]
    price_change: FiniteFloat
    price_change_pct: FiniteFloat
    days_since_release: NonNegativeFloat
    day_of_week: Annotated[int, Field(ge=0, le=6)]
    month: Annotated[int, Field(ge=1, le=12)]
    is_weekend: Annotated[int, Field(ge=0, le=1)]
    is_event: Annotated[int, Field(ge=0, le=1)]
    dow_sin: Annotated[FiniteFloat, Field(ge=-1, le=1)]
    dow_cos: Annotated[FiniteFloat, Field(ge=-1, le=1)]
    month_sin: Annotated[FiniteFloat, Field(ge=-1, le=1)]
    month_cos: Annotated[FiniteFloat, Field(ge=-1, le=1)]
    dept_id: Annotated[str, Field(min_length=1)]
    cat_id: Annotated[str, Field(min_length=1)]
    store_id: Annotated[str, Field(min_length=1)]
    state_id: Annotated[str, Field(min_length=1)]


class PredictionRequest(BaseModel):
    """Demand forecast inputs and current inventory position."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    product: Annotated[str, Field(min_length=1)]
    current_stock: Annotated[int, Field(alias="currentStock", ge=0)]
    safety_stock: Annotated[int, Field(alias="safetyStock", ge=0)]
    features: FeatureData


class PredictionResponse(BaseModel):
    """Seven-day forecast and inventory action returned to the client."""

    model_config = ConfigDict(populate_by_name=True)

    product: str
    predicted_demand_7_days: int = Field(alias="predictedDemand7Days")
    current_stock: int = Field(alias="currentStock")
    safety_stock: int = Field(alias="safetyStock")
    recommended_reorder: int = Field(alias="recommendedReorder")
    risk_level: Literal["LOW", "MEDIUM", "HIGH"] = Field(alias="riskLevel")
