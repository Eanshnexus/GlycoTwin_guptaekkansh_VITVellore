"""
GlycoTwin Patient & Observation Schemas.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from backend.app.schemas.common import PaginationMeta

class GlucoseStats(BaseModel):
    mean: float = Field(..., description="Mean observed glucose in mg/dL")
    std: float = Field(..., description="Standard deviation of observed glucose in mg/dL")
    min: float = Field(..., description="Minimum observed glucose in mg/dL")
    max: float = Field(..., description="Maximum observed glucose in mg/dL")
    tir_percentage: float = Field(..., description="Time In Range (70-180 mg/dL) percentage")
    tbr_percentage: float = Field(..., description="Time Below Range (<70 mg/dL) percentage")
    tar_percentage: float = Field(..., description="Time Above Range (>180 mg/dL) percentage")

class PatientListItem(BaseModel):
    participant_id: str = Field(..., description="Anonymized participant identifier")
    observation_count: int = Field(..., description="Total observation count")
    start_time: str = Field(..., description="Earliest recorded observation timestamp")
    end_time: str = Field(..., description="Latest recorded observation timestamp")
    duration_days: float = Field(..., description="Duration of recording in days")
    available_modalities: List[str] = Field(..., description="Data modalities recorded (CGM, HR, CSII, etc.)")
    has_historical_predictions: bool = Field(True, description="Whether out-of-fold historical predictions exist")

class PatientListResponse(BaseModel):
    patients: List[PatientListItem]
    pagination: PaginationMeta

class PatientDetail(BaseModel):
    participant_id: str = Field(..., description="Anonymized participant identifier")
    observation_count: int = Field(..., description="Total observation count")
    start_time: str = Field(..., description="Earliest recorded observation timestamp")
    end_time: str = Field(..., description="Latest recorded observation timestamp")
    duration_days: float = Field(..., description="Duration of recording in days")
    glucose_stats: GlucoseStats = Field(..., description="Glucose distribution statistics")
    available_modalities: List[str] = Field(..., description="Data modalities recorded")
    has_historical_predictions: bool = Field(..., description="Whether out-of-fold predictions exist")
    risk_predictions_count: int = Field(..., description="Total Task A historical predictions")
    onset_predictions_count: int = Field(..., description="Total Task B historical predictions")

class ObservationItem(BaseModel):
    time: str = Field(..., description="Observation timestamp (ISO format)")
    glucose: float = Field(..., description="Current sensor glucose in mg/dL")
    calories: Optional[float] = Field(None, description="Recent 30m expenditure in kcal")
    steps: Optional[float] = Field(None, description="Recent 30m step count")
    heart_rate: Optional[float] = Field(None, description="Recent 30m mean heart rate in bpm")
    basal_rate: Optional[float] = Field(None, description="Active CSII basal rate in U/hr")
    bolus_volume: Optional[float] = Field(None, description="Recent cumulative bolus in Units")
    carb_input: Optional[float] = Field(None, description="Recent cumulative carbohydrate intake in grams")

class ObservationResponse(BaseModel):
    participant_id: str
    observations: List[ObservationItem]
    pagination: PaginationMeta
