"""
GlycoTwin FastAPI Dependencies.
Provides dependency injection providers for DataService, ModelService, and EvaluationService.
"""
from backend.app.services.data_service import data_service, DataService
from backend.app.services.model_service import model_service, ModelService
from backend.app.services.evaluation_service import evaluation_service, EvaluationService

def get_data_service() -> DataService:
    if not data_service.is_ready:
        data_service.initialize()
    return data_service

def get_model_service() -> ModelService:
    model_service.initialize()
    return model_service

def get_evaluation_service() -> EvaluationService:
    evaluation_service.initialize()
    return evaluation_service
