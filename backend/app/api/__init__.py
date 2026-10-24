"""
GlycoTwin API Routing Package.
"""
from fastapi import APIRouter

from backend.app.api.health import router as health_router
from backend.app.api.metadata import router as metadata_router
from backend.app.api.patients import router as patients_router
from backend.app.api.predictions import router as predictions_router
from backend.app.api.evaluation import router as evaluation_router
from backend.app.api.personalisation import router as personalisation_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(metadata_router)
api_router.include_router(patients_router)
api_router.include_router(predictions_router)
api_router.include_router(evaluation_router)
api_router.include_router(personalisation_router)

__all__ = ["api_router"]
