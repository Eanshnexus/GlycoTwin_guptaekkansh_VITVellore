"""
GlycoTwin Prediction Schemas.
Enforces the critical scientific distinction between:
- Mode A: Historical Cross-Validated Out-of-Fold Predictions (retrospective evaluation)
- Mode B: Model Deployment Inference (forward evaluation on supplied feature vector)
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from backend.app.schemas.common import PaginationMeta

class HistoricalPredictionItem(BaseModel):
    participant_id: str = Field(..., description="Anonymized participant ID")
    time: str = Field(..., description="Prediction timestamp")
    task: str = Field(..., description="Task name (task_a_future_hypo or task_b_impending_onset)")
    model: str = Field(..., description="Model name (rule_based, logistic_regression, xgboost)")
    predicted_probability: float = Field(..., description="Predicted probability of event within 30 minutes")
    predicted_class: int = Field(..., description="Predicted binary class using calibrated threshold")
    operational_threshold: float = Field(..., description="Decision threshold applied")
    true_target: Optional[int] = Field(None, description="Actual observed outcome (retrospective evaluation only)")
    cv_fold: Optional[int] = Field(None, description="Held-out validation fold identifier (1-5)")
    horizon_minutes: int = Field(30, description="Forward forecast horizon in minutes")
    evaluation_type: str = Field("out_of_fold_cross_validation", description="Evaluation methodology provenance")

class HistoricalPredictionResponse(BaseModel):
    participant_id: str
    task: str
    predictions: List[HistoricalPredictionItem]
    pagination: PaginationMeta

class InferenceRequest(BaseModel):
    task: str = Field(..., description="Prediction task: 'risk' / 'task_a_future_hypo' or 'onset' / 'task_b_impending_onset'")
    model: str = Field("xgboost", description="Model architecture: 'rule_based', 'logistic_regression', or 'xgboost'")
    features: Dict[str, float] = Field(..., description="Dictionary mapping all 28 feature names to finite numeric values")
    prediction_time: Optional[str] = Field(None, description="Timestamp for the prediction observation (defaults to current UTC)")
    participant_id: Optional[str] = Field(None, description="Optional metadata identifier (strictly excluded from model features)")

class InferenceResponse(BaseModel):
    task: str = Field(..., description="Canonical task name evaluated")
    model: str = Field(..., description="Model architecture utilized")
    prediction_time: str = Field(..., description="Timestamp of inference")
    horizon_minutes: int = Field(30, description="Forward forecast horizon in minutes")
    glucose_current: float = Field(..., description="Current glucose value at prediction time in mg/dL")
    predicted_probability: float = Field(..., description="Model estimated event probability [0.0 - 1.0]")
    predicted_class: int = Field(..., description="Binary alert decision (1 = Alert, 0 = Normal)")
    operational_threshold: float = Field(..., description="Operational decision threshold applied")
    feature_schema_version: str = Field("1.0.0 (28 features)", description="Feature manifest version reference")
    inference_status: str = Field("success", description="Execution status")
    limitation_notice: str = Field(
        "Research prototype inference. Not clinically validated for diagnostic or standalone treatment decisions.",
        description="Clinical and regulatory safety notice"
    )
