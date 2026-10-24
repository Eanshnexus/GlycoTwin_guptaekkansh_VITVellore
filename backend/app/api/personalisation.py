"""
GlycoTwin Personalisation Evaluation API Route.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException

from backend.app.schemas.evaluation import PersonalisationResponse
from backend.app.dependencies import get_evaluation_service
from backend.app.services.evaluation_service import EvaluationService

router = APIRouter(prefix="/models/personalisation", tags=["Personalisation"])

@router.get("", response_model=PersonalisationResponse, summary="Retrieve verified chronological personalisation comparisons")
def get_personalisation_metrics(
    participant_id: Optional[str] = Query(None, description="Optional participant ID filter (e.g. HUPA0001P)"),
    eval_svc: EvaluationService = Depends(get_evaluation_service)
) -> PersonalisationResponse:
    """
    Returns audit-verified personalisation comparison results evaluated using a strict
    chronological split with a 30-minute target-horizon purge gap.
    """
    try:
        summary = eval_svc.get_personalisation_summary(participant_id=participant_id)
        return PersonalisationResponse(**summary)
    except KeyError as ke:
        raise HTTPException(status_code=404, detail=str(ke))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load personalisation metrics: {str(e)}")
