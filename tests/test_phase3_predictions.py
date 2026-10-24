"""
Unit Tests for Phase 3 Model Inference & Prediction Service.
Tests model loading, feature schema validation, leakage prevention, and Task B condition enforcement.
"""
import pytest
import numpy as np
from backend.app.services.model_service import ModelService
from ml.model_config import FEATURE_COLUMNS

@pytest.fixture(scope="module")
def model_service():
    ms = ModelService()
    ms.initialize()
    return ms

@pytest.fixture
def valid_features():
    """Generates a complete, valid 28-feature dictionary."""
    f = {col: 0.0 for col in FEATURE_COLUMNS}
    # Set realistic physiological values
    f["glucose_current"] = 110.0
    f["glucose_lag_5m"] = 112.0
    f["glucose_lag_10m"] = 115.0
    f["glucose_lag_15m"] = 118.0
    f["glucose_lag_30m"] = 125.0
    f["glucose_lag_60m"] = 135.0
    f["glucose_change_5m"] = -2.0
    f["glucose_change_15m"] = -8.0
    f["glucose_change_30m"] = -15.0
    f["glucose_slope_15m"] = -8.0 / 15.0
    f["glucose_slope_30m"] = -15.0 / 30.0
    f["glucose_mean_15m"] = 115.0
    f["glucose_mean_30m"] = 120.0
    f["glucose_mean_60m"] = 125.0
    f["glucose_std_30m"] = 5.0
    f["glucose_std_60m"] = 8.0
    f["glucose_min_30m"] = 110.0
    f["glucose_max_30m"] = 125.0
    f["hour_sin"] = 0.5
    f["hour_cos"] = 0.86
    f["weekday_sin"] = 0.0
    f["weekday_cos"] = 1.0
    f["recent_calories"] = 10.0
    f["recent_steps"] = 50.0
    f["recent_heart_rate"] = 72.0
    f["recent_basal_rate"] = 0.08
    f["recent_bolus_volume"] = 0.0
    f["recent_carb_input"] = 0.0
    return f

def test_model_service_initialization(model_service):
    status = model_service.get_model_status()
    assert status["rule_based"] is True
    assert status["logistic_regression"] is True
    assert status["xgboost"] is True

def test_task_a_inference_xgboost(model_service, valid_features):
    res = model_service.validate_and_predict(
        task="risk",
        model_name="xgboost",
        features=valid_features
    )
    assert res["task"] == "task_a_future_hypo"
    assert res["model"] == "xgboost"
    assert 0.0 <= res["predicted_probability"] <= 1.0
    assert res["predicted_class"] in [0, 1]
    assert res["operational_threshold"] == 0.8707

def test_task_b_inference_logistic_regression(model_service, valid_features):
    res = model_service.validate_and_predict(
        task="onset",
        model_name="logistic_regression",
        features=valid_features
    )
    assert res["task"] == "task_b_impending_onset"
    assert res["model"] == "logistic_regression"
    assert 0.0 <= res["predicted_probability"] <= 1.0
    assert res["predicted_class"] in [0, 1]
    assert res["operational_threshold"] == 0.8743

def test_task_b_inference_rule_based(model_service, valid_features):
    res = model_service.validate_and_predict(
        task="task_b_impending_onset",
        model_name="rule_based",
        features=valid_features
    )
    assert res["task"] == "task_b_impending_onset"
    assert res["model"] == "rule_based"
    assert 0.0 <= res["predicted_probability"] <= 1.0

def test_task_b_condition_enforcement(model_service, valid_features):
    # Setting glucose_current < 70 mg/dL must trigger ValueError
    features_low = dict(valid_features)
    features_low["glucose_current"] = 65.0
    with pytest.raises(ValueError, match="conditionally on current glucose being >= 70.0"):
        model_service.validate_and_predict(
            task="onset",
            model_name="xgboost",
            features=features_low
        )

def test_missing_feature_rejection(model_service, valid_features):
    f_missing = dict(valid_features)
    del f_missing["glucose_slope_15m"]
    with pytest.raises(ValueError, match="Missing required feature fields"):
        model_service.validate_and_predict(
            task="risk",
            model_name="xgboost",
            features=f_missing
        )

def test_leakage_field_rejection(model_service, valid_features):
    f_leak = dict(valid_features)
    f_leak["target_hypo_30m"] = 1.0
    with pytest.raises(ValueError, match="Leakage violation"):
        model_service.validate_and_predict(
            task="risk",
            model_name="xgboost",
            features=f_leak
        )

def test_metadata_field_rejection(model_service, valid_features):
    f_meta = dict(valid_features)
    f_meta["participant_id"] = "HUPA0001P"
    with pytest.raises(ValueError, match="Leakage violation"):
        model_service.validate_and_predict(
            task="risk",
            model_name="xgboost",
            features=f_meta
        )

def test_non_finite_feature_rejection(model_service, valid_features):
    f_nan = dict(valid_features)
    f_nan["glucose_std_30m"] = float("nan")
    with pytest.raises(ValueError, match="non-finite value"):
        model_service.validate_and_predict(
            task="risk",
            model_name="xgboost",
            features=f_nan
        )
