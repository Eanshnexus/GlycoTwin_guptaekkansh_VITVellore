"""
GlycoTwin Patients & Observations API Routes.
Exposes verified participant summaries, time-series observations, and historical out-of-fold predictions.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.schemas.patients import (
    PatientListResponse,
    PatientDetail,
    ObservationResponse
)
from backend.app.schemas.predictions import HistoricalPredictionResponse
from backend.app.schemas.common import PaginationMeta
from backend.app.dependencies import get_data_service
from backend.app.services.data_service import DataService

router = APIRouter(prefix="/patients", tags=["Patients"])

@router.get("", response_model=PatientListResponse, summary="List available research participants")
def list_patients(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    data_svc: DataService = Depends(get_data_service)
) -> PatientListResponse:
    """
    Returns a paginated list of anonymized research participants with recording span
    and available telemetry modalities.
    """
    items, total = data_svc.get_patients_list(page=page, page_size=page_size)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return PatientListResponse(
        patients=items,
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=total_pages
        )
    )

@router.get("/{patient_id}", response_model=PatientDetail, summary="Get summary profile for one participant")
def get_patient_detail(
    patient_id: str,
    data_svc: DataService = Depends(get_data_service)
) -> PatientDetail:
    """
    Returns complete baseline statistics, glucose distributions (TIR, TBR, TAR),
    recording duration, and prediction availability for an anonymized participant.
    """
    detail = data_svc.get_patient_detail(patient_id.strip())
    if not detail:
        raise HTTPException(
            status_code=404,
            detail=f"Participant '{patient_id}' not found in the verified dataset."
        )
    return PatientDetail(**detail)

@router.get("/{patient_id}/observations", response_model=ObservationResponse, summary="Get chronological sensor observations")
def get_patient_observations(
    patient_id: str,
    start_time: Optional[str] = Query(None, description="ISO timestamp filter lower bound (inclusive)"),
    end_time: Optional[str] = Query(None, description="ISO timestamp filter upper bound (inclusive)"),
    limit: int = Query(100, ge=1, le=1000, description="Max observations returned"),
    offset: int = Query(0, ge=0, description="Record offset for pagination"),
    data_svc: DataService = Depends(get_data_service)
) -> ObservationResponse:
    """
    Returns chronological 5-minute sensor observations for a participant, including
    sensor glucose, activity, and CSII insulin delivery.
    """
    # Verify participant existence
    if not data_svc.get_patient_detail(patient_id.strip()):
        raise HTTPException(
            status_code=404,
            detail=f"Participant '{patient_id}' not found in the verified dataset."
        )

    records, total = data_svc.get_patient_observations(
        patient_id=patient_id.strip(),
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset
    )

    page_number = (offset // limit) + 1
    total_pages = (total + limit - 1) // limit if total > 0 else 0

    return ObservationResponse(
        participant_id=patient_id.strip(),
        observations=records,
        pagination=PaginationMeta(
            page=page_number,
            page_size=limit,
            total_items=total,
            total_pages=total_pages
        )
    )

@router.get("/{patient_id}/predictions", response_model=HistoricalPredictionResponse, summary="Get historical out-of-fold predictions")
def get_patient_predictions(
    patient_id: str,
    task: Optional[str] = Query("onset", description="Task: 'risk' (Task A) or 'onset' (Task B)"),
    model: Optional[str] = Query("xgboost", description="Model: 'rule_based', 'logistic_regression', 'xgboost'"),
    limit: int = Query(100, ge=1, le=1000, description="Max predictions returned"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    data_svc: DataService = Depends(get_data_service)
) -> HistoricalPredictionResponse:
    """
    Returns verified historical predictions for an anonymized participant evaluated
    strictly using held-out out-of-fold cross-validation.
    """
    if not data_svc.get_patient_detail(patient_id.strip()):
        raise HTTPException(
            status_code=404,
            detail=f"Participant '{patient_id}' not found in the verified dataset."
        )

    records, total = data_svc.get_patient_predictions(
        patient_id=patient_id.strip(),
        task=task,
        model=model,
        limit=limit,
        offset=offset
    )

    page_number = (offset // limit) + 1
    total_pages = (total + limit - 1) // limit if total > 0 else 0

    return HistoricalPredictionResponse(
        participant_id=patient_id.strip(),
        task=task or "onset",
        predictions=records,
        pagination=PaginationMeta(
            page=page_number,
            page_size=limit,
            total_items=total,
            total_pages=total_pages
        )
    )
