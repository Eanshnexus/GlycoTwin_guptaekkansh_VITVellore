"""
GlycoTwin Metadata API Route.
"""
from fastapi import APIRouter, Depends

from backend.app.schemas.metadata import MetadataResponse
from backend.app.dependencies import get_data_service
from backend.app.services.data_service import DataService
from backend.app.config import settings, OPERATIONAL_THRESHOLDS

router = APIRouter(tags=["Metadata"])

@router.get("/metadata", response_model=MetadataResponse, summary="Frontend-compatible system metadata")
def get_metadata(data_svc: DataService = Depends(get_data_service)) -> MetadataResponse:
    """
    Returns verified clinical dataset metadata, model definitions,
    feature schemas, operational thresholds, and regulatory disclaimers.
    """
    return MetadataResponse(
        project_name=settings.app_name,
        dataset_name="HUPA-UCM Diabetes Dataset",
        dataset_provenance="Hospital Universitario Príncipe de Asturias (HUPA) & Universidad Complutense de Madrid (UCM)",
        total_participants=data_svc.total_participants,
        total_observations=data_svc.total_observations,
        prediction_horizon_minutes=30,
        hypoglycemia_threshold_mgdl=70.0,
        available_tasks={
            "task_a_future_hypo": "Unconditional prediction of glucose < 70 mg/dL within next 30 minutes",
            "task_b_impending_onset": "Prediction of impending transition < 70 mg/dL within next 30 minutes conditional on current glucose >= 70 mg/dL"
        },
        available_models=["rule_based", "logistic_regression", "xgboost"],
        feature_count=len(settings.feature_columns),
        feature_names=settings.feature_columns,
        operational_thresholds=OPERATIONAL_THRESHOLDS,
        inference_support={
            "retrospective_cross_validation_evaluation": True,
            "real_time_model_inference": True
        },
        disclaimer=(
            "GlycoTwin is an academic research prototype developed strictly for predictive modeling research. "
            "It is not a registered medical device and must not be used for standalone medical diagnosis or autonomous clinical decisions."
        )
    )
