"""
GlycoTwin Health & Readiness Schemas.
"""
from typing import Dict, Any, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall backend health status (healthy, degraded, unready)")
    app_name: str = Field(..., description="Application name")
    app_version: str = Field(..., description="Application semantic version")
    dataset_accessible: bool = Field(..., description="Whether verified modelling dataset is loaded and accessible")
    models_loaded: Dict[str, bool] = Field(..., description="Status of supported inference models")
    total_participants: int = Field(..., description="Count of loaded participants in dataset")
    total_observations: int = Field(..., description="Count of loaded records in dataset")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Health check timestamp")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional health telemetry")
