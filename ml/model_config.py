"""
GlycoTwin: Phase 2 Model & Experiment Configuration.
Defines task parameters, feature lists, cross-validation setup,
hyperparameters, and personalisation thresholds.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any

from ml.build_features import FEATURE_COLUMNS, METADATA_COLUMNS

# Target field definitions
TASK_A_TARGET = "target_hypo_30m"
TASK_B_TARGET = "is_hypo_onset_30m"

# Fields strictly excluded from feature inputs to prevent any data leakage
LEAKAGE_EXCLUSIONS: List[str] = [
    "participant_id",
    "time",
    "source_file",
    "target_hypo_30m",
    "is_hypo_onset_30m",
    "future_min_glucose_30m",
    "target_eligible",
    "is_modelling_eligible"
]

@dataclass
class ExperimentConfig:
    # Directory paths
    workspace_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    data_parquet_path: Path = field(default_factory=lambda: Path("data/processed/glycotwin_features.parquet"))
    models_dir: Path = field(default_factory=lambda: Path("artifacts/models"))
    evaluation_dir: Path = field(default_factory=lambda: Path("artifacts/evaluation/phase2"))

    # Feature configuration
    feature_columns: List[str] = field(default_factory=lambda: list(FEATURE_COLUMNS))
    leakage_exclusions: List[str] = field(default_factory=lambda: list(LEAKAGE_EXCLUSIONS))

    # Cross-validation
    n_splits: int = 5  # GroupKFold splits across 25 participants
    random_seed: int = 42

    # Classification threshold selection
    # Calibrated on training folds: e.g. target 80% sensitivity or optimal F1 on train folds
    threshold_strategy: str = "optimal_f1"  # "optimal_f1" or "fixed_0.5" or "target_sensitivity_80"

    # Personalisation Configuration
    # Fraction of each participant's chronological time-series used for personal adaptation
    personalisation_split_ratio: float = 0.30  # First 30% history for calibration, 70% for evaluation
    min_calibration_positive_events: int = 2   # Require >= 2 positive events to fit personal adapter

    # Logistic Regression hyperparameters
    logreg_params: Dict[str, Any] = field(default_factory=lambda: {
        "penalty": "l2",
        "C": 1.0,
        "solver": "lbfgs",
        "max_iter": 1000,
        "class_weight": "balanced",
        "random_state": 42
    })

    # XGBoost hyperparameters
    xgb_params: Dict[str, Any] = field(default_factory=lambda: {
        "n_estimators": 100,
        "max_depth": 4,
        "learning_rate": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "eval_metric": "logloss",
        "random_state": 42,
        "n_jobs": -1
    })

DEFAULT_EXPERIMENT_CONFIG = ExperimentConfig()
