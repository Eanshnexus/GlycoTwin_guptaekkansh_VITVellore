"""
GlycoTwin Backend Configuration.
Centralized settings, path resolution, task registry, and operational thresholds.
"""
from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from ml.model_config import FEATURE_COLUMNS, LEAKAGE_EXCLUSIONS

# Canonical task aliases
TASK_ALIASES = {
    "risk": "task_a_future_hypo",
    "task_a": "task_a_future_hypo",
    "task_a_future_hypo": "task_a_future_hypo",
    "task_a_all_risk": "task_a_future_hypo",
    "all_risk": "task_a_future_hypo",
    "onset": "task_b_impending_onset",
    "task_b": "task_b_impending_onset",
    "task_b_impending_onset": "task_b_impending_onset"
}

# Verified operational classification thresholds from Phase 2 population evaluation
OPERATIONAL_THRESHOLDS: Dict[str, Dict[str, float]] = {
    "task_a_future_hypo": {
        "rule_based": 0.5949,
        "logistic_regression": 0.8578,
        "xgboost": 0.8707
    },
    "task_b_impending_onset": {
        "rule_based": 0.5506,
        "logistic_regression": 0.8743,
        "xgboost": 0.9148
    }
}

class Settings(BaseModel):
    # App Information
    app_name: str = "GlycoTwin API"
    app_version: str = "1.0.0"
    app_description: str = (
        "Personalised Glucose Digital Twin API for predictive diabetes management, "
        "providing verified dataset access, historical cross-validation predictions, "
        "and real-time ML risk and onset inference."
    )
    api_prefix: str = "/api"
    debug: bool = False

    # Server binding
    host: str = "127.0.0.1"
    port: int = 8000

    # CORS
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

    # Filesystem Paths (resolved relative to repository root)
    workspace_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent)

    @property
    def data_parquet_path(self) -> Path:
        return self.workspace_root / "data" / "processed" / "glycotwin_features.parquet"

    @property
    def models_dir(self) -> Path:
        return self.workspace_root / "artifacts" / "models"

    @property
    def evaluation_audit_dir(self) -> Path:
        return self.workspace_root / "artifacts" / "evaluation" / "phase2_audit_run"

    @property
    def evaluation_phase2_dir(self) -> Path:
        return self.workspace_root / "artifacts" / "evaluation" / "phase2"

    @property
    def feature_manifest_path(self) -> Path:
        return self.workspace_root / "artifacts" / "data_dictionary" / "feature_manifest.json"

    # Feature definitions
    feature_columns: List[str] = Field(default_factory=lambda: list(FEATURE_COLUMNS))
    leakage_exclusions: List[str] = Field(default_factory=lambda: list(LEAKAGE_EXCLUSIONS))

settings = Settings()
