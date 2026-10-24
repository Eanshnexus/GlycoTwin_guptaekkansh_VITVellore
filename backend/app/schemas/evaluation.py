"""
GlycoTwin Evaluation & Personalisation Schemas.
Exposes authoritative Phase 2 cross-validation performance and audit-corrected personalisation metrics.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class MetricScoreSet(BaseModel):
    roc_auc: Optional[float] = Field(None, description="Receiver Operating Characteristic AUC (ranking discrimination)")
    average_precision: Optional[float] = Field(None, description="Average Precision / PR-AUC")
    f1_score: Optional[float] = Field(None, description="F1 Score at operational threshold")
    sensitivity: Optional[float] = Field(None, description="True Positive Rate / Recall / Sensitivity")
    specificity: Optional[float] = Field(None, description="True Negative Rate / Specificity")
    precision: Optional[float] = Field(None, description="Positive Predictive Value")
    brier_score: Optional[float] = Field(None, description="Mean squared error of probabilities (calibration score)")

class ModelEvaluationSummary(BaseModel):
    model: str = Field(..., description="Model name (rule_based, logistic_regression, xgboost)")
    task: str = Field(..., description="Evaluation task")
    evaluation_method: str = Field("5-Fold GroupKFold Cross-Validation across 25 participants", description="Partitioning method")
    sample_count: int = Field(..., description="Total evaluated out-of-fold records")
    positive_count: int = Field(..., description="Total positive prediction windows in evaluation set")
    negative_count: int = Field(..., description="Total negative prediction windows in evaluation set")
    operational_threshold: float = Field(..., description="Calibrated operational decision threshold")
    pooled_metrics: MetricScoreSet = Field(..., description="Pooled metrics across all held-out observations")
    macro_metrics: Dict[str, Optional[float]] = Field(..., description="Participant-balanced macro-averaged summary")
    notes: str = Field(..., description="Methodological notes")

class EvaluationResponse(BaseModel):
    task: str
    target_column: str
    models: List[ModelEvaluationSummary]
    caveats: List[str]

class PersonalisationItem(BaseModel):
    participant_id: str
    adaptation_status: str = Field(..., description="'personalised' or 'fallback_insufficient_events'")
    calib_rows_total: int = Field(..., description="Original 30% calibration row count")
    calib_rows_purged: int = Field(..., description="Rows purged to prevent 30m forward-horizon overlap")
    calib_rows_usable: int = Field(..., description="Net usable calibration rows")
    calib_positives: int = Field(..., description="Positive prediction windows in calibration period")
    eval_rows: int = Field(..., description="Evaluation segment rows (identical for both models)")
    eval_positives: int = Field(..., description="Evaluation segment positive prediction windows")
    t_pop: float = Field(..., description="Population model threshold")
    t_pers: float = Field(..., description="Personalised adapter mapped threshold")
    pop_roc_auc: Optional[float] = Field(None, description="Unadapted population ROC-AUC")
    pers_roc_auc: Optional[float] = Field(None, description="Personalised model ROC-AUC")
    delta_roc_auc: Optional[float] = Field(None, description="Change in ROC-AUC")
    pop_avg_prec: Optional[float] = Field(None, description="Unadapted population Average Precision")
    pers_avg_prec: Optional[float] = Field(None, description="Personalised Average Precision")
    delta_avg_prec: Optional[float] = Field(None, description="Change in Average Precision")
    pop_f1: Optional[float] = Field(None, description="Unadapted population F1 Score")
    pers_f1: Optional[float] = Field(None, description="Personalised F1 Score")
    delta_f1: Optional[float] = Field(None, description="Change in F1 Score")
    pop_brier: Optional[float] = Field(None, description="Unadapted population Brier score")
    pers_brier: Optional[float] = Field(None, description="Personalised Brier score")
    delta_brier: Optional[float] = Field(None, description="Change in Brier score (negative = improved calibration)")

class PersonalisationResponse(BaseModel):
    task: str = Field("task_b_impending_onset", description="Task evaluated for personalisation")
    adaptation_method: str = Field("Platt Scaling (1D Logistic Recalibration on Population Log-Odds)", description="Adapter algorithm")
    purge_gap_minutes: int = Field(30, description="Purge gap duration between calibration and evaluation segments")
    total_participants: int = Field(25, description="Total participants evaluated")
    successful_adaptations: int = Field(..., description="Count of successfully adapted participants")
    fallback_adaptations: int = Field(..., description="Count of participants falling back to population model")
    participants: List[PersonalisationItem]
    summary_deltas: Dict[str, Any] = Field(..., description="Cohort aggregate delta summary")
    caveats: List[str] = Field(..., description="Scientific limitations and calibration notices")
