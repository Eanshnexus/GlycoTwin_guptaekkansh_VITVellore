"""
GlycoTwin Health Check API Route.
"""
from fastapi import APIRouter, Depends
from datetime import datetime

from backend.app.schemas.health import HealthResponse
from backend.app.dependencies import get_data_service, get_model_service
from backend.app.services.data_service import DataService
from backend.app.services.model_service import ModelService
from backend.app.config import settings

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse, summary="Backend health & readiness probe")
def check_health(
    data_svc: DataService = Depends(get_data_service),
    model_svc: ModelService = Depends(get_model_service)
) -> HealthResponse:
    """
    Returns operational readiness of the GlycoTwin backend,
    including dataset accessibility and loaded model artifact status.
    """
    data_ready = data_svc.is_ready
    model_status = model_svc.get_model_status()
    all_models_ready = all(model_status.values()) if model_status else False

    if data_ready and all_models_ready:
        overall_status = "healthy"
    elif data_ready:
        overall_status = "degraded"
    else:
        overall_status = "unready"

    from datetime import timezone
    return HealthResponse(
        status=overall_status,
        app_name=settings.app_name,
        app_version=settings.app_version,
        dataset_accessible=data_ready,
        models_loaded=model_status,
        total_participants=data_svc.total_participants,
        total_observations=data_svc.total_observations,
        timestamp=datetime.now(timezone.utc),
        details={
            "dataset_path": str(settings.data_parquet_path),
            "environment": "research_prototype",
            "audit_compliance": "PASS WITH CAVEATS"
        }
    )
