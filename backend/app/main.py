"""
GlycoTwin FastAPI Application Entrypoint.
Initializes data, models, CORS middleware, API routers, and lifecycle events.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config import settings
from backend.app.api import api_router
from backend.app.services.data_service import data_service
from backend.app.services.model_service import model_service
from backend.app.services.evaluation_service import evaluation_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes cached dataset, serialized models, and evaluation artifacts at application startup."""
    print("=" * 60)
    print("Initializing GlycoTwin Backend Services...")
    try:
        data_service.initialize()
        print(f"DataService initialized: {data_service.total_observations:,} records across {data_service.total_participants} participants.")
    except Exception as e:
        print(f"Warning: DataService initialization failed: {e}")

    try:
        model_service.initialize()
        print(f"ModelService initialized: {model_service.get_model_status()}")
    except Exception as e:
        print(f"Warning: ModelService initialization failed: {e}")

    try:
        evaluation_service.initialize()
        print("EvaluationService initialized.")
    except Exception as e:
        print(f"Warning: EvaluationService initialization failed: {e}")

    print("GlycoTwin API ready for incoming requests.")
    print("=" * 60)
    yield
    print("Shutting down GlycoTwin Backend Services...")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS Configuration for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Mount API Router under /api
app.include_router(api_router, prefix=settings.api_prefix)

@app.get("/", tags=["Root"])
def root_index():
    return JSONResponse({
        "project": settings.app_name,
        "version": settings.app_version,
        "description": "Personalised Glucose Digital Twin API",
        "documentation": "/docs",
        "health_check": f"{settings.api_prefix}/health",
        "metadata": f"{settings.api_prefix}/metadata",
        "status": "operational"
    })
