"""
GlycoTwin Real-Time Model Inference API Route.
Mode B: Forward Model Inference on supplied feature vectors.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.schemas.predictions import InferenceRequest, InferenceResponse
from backend.app.dependencies import get_model_service
from backend.app.services.model_service import ModelService

router = APIRouter(prefix="/predictions", tags=["Predictions & Inference"])

@router.post("", response_model=InferenceResponse, status_code=status.HTTP_200_OK, summary="Execute forward model inference")
def predict_glucose_risk(
    request: InferenceRequest,
    model_svc: ModelService = Depends(get_model_service)
) -> InferenceResponse:
    """
    Executes real-time model inference using an approved deployment model artifact.
    
    Validation & Safety Checks:
    - Verifies the selected task and model exist.
    - Requires exactly 28 numeric features.
    - Rejects target-derived fields, future glucose, or metadata fields.
    - For Task B (Impending Onset), enforces current glucose >= 70 mg/dL.
    - Applies the calibrated operational decision threshold to emit binary alert.
    """
    try:
        result = model_svc.validate_and_predict(
            task=request.task,
            model_name=request.model,
            features=request.features,
            prediction_time=request.prediction_time,
            participant_id=request.participant_id
        )
        return InferenceResponse(**result)
    except ValueError as ve:
        # Client validation error (missing features, leakage fields, Task B condition violated)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve)
        )
    except RuntimeError as re:
        # Model runtime execution error
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(re)
        )
