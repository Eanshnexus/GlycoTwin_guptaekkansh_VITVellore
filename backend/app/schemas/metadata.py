"""
GlycoTwin Metadata Schemas.
"""
from typing import List, Dict, Any
from pydantic import BaseModel, Field

class MetadataResponse(BaseModel):
    project_name: str = Field(..., description="Project name")
    dataset_name: str = Field(..., description="Underlying clinical dataset name")
    dataset_provenance: str = Field(..., description="Clinical research source and licensing")
    total_participants: int = Field(..., description="Total available anonymized participants")
    total_observations: int = Field(..., description="Total verified 5-minute grid observations")
    prediction_horizon_minutes: int = Field(30, description="Forward prediction window in minutes")
    hypoglycemia_threshold_mgdl: float = Field(70.0, description="Hypoglycemia definition threshold in mg/dL")
    available_tasks: Dict[str, str] = Field(..., description="Map of task identifiers to definitions")
    available_models: List[str] = Field(..., description="List of evaluated model families")
    feature_count: int = Field(..., description="Count of input features utilized by models")
    feature_names: List[str] = Field(..., description="Ordered list of model feature names")
    operational_thresholds: Dict[str, Dict[str, float]] = Field(..., description="Calibrated decision thresholds")
    inference_support: Dict[str, bool] = Field(..., description="Capabilities supported (retrospective vs real-time inference)")
    disclaimer: str = Field(..., description="Regulatory and research-prototype notice")
