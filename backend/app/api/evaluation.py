"""
GlycoTwin Model Evaluation API Route.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException

from backend.app.schemas.evaluation import EvaluationResponse
from backend.app.dependencies import get_evaluation_service
from backend.app.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/models/evaluation", tags=["Model Evaluation"])

@router.get("", response_model=EvaluationResponse, summary="Retrieve verified population cross-validation metrics")
def get_model_evaluation(
    task: Optional[str] = Query("onset", description="Prediction task: 'risk' (Task A) or 'onset' (Task B)"),
    eval_svc: EvaluationService = Depends(get_evaluation_service)
) -> EvaluationResponse:
    """
    Returns verified population evaluation metrics across models (Rule-based, Logistic Regression, XGBoost)
    evaluated using 5-Fold GroupKFold cross-validation across participants.
    """
    try:
        summary = eval_svc.get_evaluation_summary(task=task)
        return EvaluationResponse(**summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load evaluation metrics: {str(e)}")
