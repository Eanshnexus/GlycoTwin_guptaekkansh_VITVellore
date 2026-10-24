"""
GlycoTwin Model Service.
Manages model loading, feature schema validation, leakage prevention, and real-time model inference.
Enforces the critical boundary:
- Mode B deployment inference vs Mode A retrospective out-of-fold predictions.
"""
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
from datetime import datetime
import joblib
import numpy as np
import pandas as pd

from backend.app.config import settings, TASK_ALIASES, OPERATIONAL_THRESHOLDS
from ml.model_config import FEATURE_COLUMNS, LEAKAGE_EXCLUSIONS
from ml.train_baselines import RuleBasedHypoBaseline

class ModelService:
    def __init__(self):
        self._models: Dict[str, Dict[str, Any]] = {
            "task_a_future_hypo": {},
            "task_b_impending_onset": {}
        }
        self._load_status: Dict[str, bool] = {}
        self._is_initialized = False

    def initialize(self):
        """Loads serialized deployment model artifacts."""
        if self._is_initialized:
            return

        models_dir = settings.models_dir

        # 1. Rule-Based Baselines (always available)
        self._models["task_a_future_hypo"]["rule_based"] = RuleBasedHypoBaseline()
        self._models["task_b_impending_onset"]["rule_based"] = RuleBasedHypoBaseline()
        self._load_status["rule_based"] = True

        # 2. Logistic Regression Models
        lr_dir = models_dir / "logistic_regression"
        lr_a_path = lr_dir / "model_task_a_risk.joblib"
        lr_b_path = lr_dir / "model_task_b_onset.joblib"

        try:
            if lr_a_path.exists():
                self._models["task_a_future_hypo"]["logistic_regression"] = joblib.load(lr_a_path)
            if lr_b_path.exists():
                self._models["task_b_impending_onset"]["logistic_regression"] = joblib.load(lr_b_path)
            self._load_status["logistic_regression"] = (
                "logistic_regression" in self._models["task_a_future_hypo"] and
                "logistic_regression" in self._models["task_b_impending_onset"]
            )
        except Exception as e:
            self._load_status["logistic_regression"] = False

        # 3. XGBoost Models
        xgb_dir = models_dir / "xgboost"
        xgb_a_path = xgb_dir / "model_task_a_risk.joblib"
        xgb_b_path = xgb_dir / "model_task_b_onset.joblib"

        try:
            if xgb_a_path.exists():
                self._models["task_a_future_hypo"]["xgboost"] = joblib.load(xgb_a_path)
            if xgb_b_path.exists():
                self._models["task_b_impending_onset"]["xgboost"] = joblib.load(xgb_b_path)
            self._load_status["xgboost"] = (
                "xgboost" in self._models["task_a_future_hypo"] and
                "xgboost" in self._models["task_b_impending_onset"]
            )
        except Exception as e:
            self._load_status["xgboost"] = False

        self._is_initialized = True

    def get_model_status(self) -> Dict[str, bool]:
        if not self._is_initialized:
            self.initialize()
        return dict(self._load_status)

    def validate_and_predict(
        self,
        task: str,
        model_name: str,
        features: Dict[str, Any],
        prediction_time: Optional[str] = None,
        participant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validates the incoming feature vector and executes model inference.
        Enforces:
        - Task existence
        - Model existence
        - Exclusion of forbidden leakage fields
        - Completeness of 28 feature inputs
        - Numeric finite checks
        - Task B condition: glucose_current >= 70 mg/dL
        """
        if not self._is_initialized:
            self.initialize()

        # 1. Validate Task
        task_clean = task.lower().strip()
        canonical_task = TASK_ALIASES.get(task_clean)
        if not canonical_task or canonical_task not in self._models:
            raise ValueError(f"Unknown prediction task '{task}'. Supported tasks: 'risk' (Task A), 'onset' (Task B).")

        # 2. Validate Model Architecture
        model_clean = model_name.lower().strip()
        task_models = self._models[canonical_task]
        if model_clean not in task_models:
            supported = list(task_models.keys())
            raise ValueError(f"Model '{model_name}' is not loaded for task '{canonical_task}'. Available models: {supported}")

        model_artifact = task_models[model_clean]

        # 3. Check for Forbidden Leakage and Metadata Fields in Features
        for key in features.keys():
            if key in LEAKAGE_EXCLUSIONS:
                raise ValueError(
                    f"Leakage violation: Forbidden target/metadata field '{key}' cannot be supplied as a model feature."
                )

        # 4. Check Completeness of 28 Features
        missing_features = [f for f in FEATURE_COLUMNS if f not in features]
        if missing_features:
            raise ValueError(
                f"Missing required feature fields: {missing_features}. Exactly 28 verified features are required."
            )

        # 5. Check Finite Numeric Values
        feature_values = {}
        for col in FEATURE_COLUMNS:
            val = features[col]
            try:
                f_val = float(val)
            except (TypeError, ValueError):
                raise ValueError(f"Feature '{col}' must be a valid numeric value; received '{val}'.")

            if np.isnan(f_val) or np.isinf(f_val):
                raise ValueError(f"Feature '{col}' contains non-finite value ({val}). All features must be finite numbers.")
            feature_values[col] = f_val

        # 6. Enforce Task B Eligibility: Current Glucose >= 70 mg/dL
        glucose_curr = feature_values["glucose_current"]
        if canonical_task == "task_b_impending_onset" and glucose_curr < 70.0:
            raise ValueError(
                f"Task B (Impending Onset) is defined conditionally on current glucose being >= 70.0 mg/dL. "
                f"Current glucose is {glucose_curr:.1f} mg/dL (already in hypoglycemia). Use Task A for unconditional future risk."
            )

        # 7. Construct Feature Matrix with Strict Column Ordering
        X_df = pd.DataFrame([feature_values])[FEATURE_COLUMNS]

        # 8. Execute Inference
        try:
            if hasattr(model_artifact, "predict_proba"):
                prob = float(model_artifact.predict_proba(X_df)[:, 1][0])
            else:
                prob = float(model_artifact.predict(X_df)[0])
        except Exception as e:
            raise RuntimeError(f"Error during model execution: {str(e)}")

        # 9. Apply Verified Operational Classification Threshold
        op_thresh = OPERATIONAL_THRESHOLDS.get(canonical_task, {}).get(model_clean, 0.5)
        pred_class = int(prob >= op_thresh)

        from datetime import timezone
        t_now = prediction_time if prediction_time else datetime.now(timezone.utc).isoformat()

        return {
            "task": canonical_task,
            "model": model_clean,
            "prediction_time": t_now,
            "horizon_minutes": 30,
            "glucose_current": round(glucose_curr, 1),
            "predicted_probability": round(prob, 4),
            "predicted_class": pred_class,
            "operational_threshold": round(op_thresh, 4),
            "feature_schema_version": "1.0.0 (28 features)",
            "inference_status": "success",
            "limitation_notice": (
                "Research prototype inference. Model trained on adult Type 1 diabetes cohort (HUPA-UCM). "
                "Not clinically certified for autonomous medical diagnosis or therapy control."
            )
        }

model_service = ModelService()
