"""Pydantic request and response schemas for the API."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response returned by the health-check endpoint."""

    status: str
    service: str

