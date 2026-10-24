"""
Integration & End-to-End API Tests for Phase 3 FastAPI Backend.
Uses FastAPI TestClient to test all endpoints, request validation, error responses, and schemas.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from ml.model_config import FEATURE_COLUMNS

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def valid_features():
    """Generates a complete, valid 28-feature dictionary."""
    f = {col: 0.0 for col in FEATURE_COLUMNS}
    f["glucose_current"] = 120.0
    f["glucose_lag_5m"] = 122.0
    f["glucose_lag_10m"] = 124.0
    f["glucose_lag_15m"] = 128.0
    f["glucose_lag_30m"] = 132.0
    f["glucose_lag_60m"] = 140.0
    f["glucose_change_5m"] = -2.0
    f["glucose_change_15m"] = -8.0
    f["glucose_change_30m"] = -12.0
    f["glucose_slope_15m"] = -8.0 / 15.0
    f["glucose_slope_30m"] = -12.0 / 30.0
    f["glucose_mean_15m"] = 124.0
    f["glucose_mean_30m"] = 128.0
    f["glucose_mean_60m"] = 135.0
    f["glucose_std_30m"] = 4.5
    f["glucose_std_60m"] = 6.2
    f["glucose_min_30m"] = 120.0
    f["glucose_max_30m"] = 135.0
    f["hour_sin"] = 0.5
    f["hour_cos"] = 0.86
    f["weekday_sin"] = 0.0
    f["weekday_cos"] = 1.0
    f["recent_calories"] = 12.0
    f["recent_steps"] = 60.0
    f["recent_heart_rate"] = 74.0
    f["recent_basal_rate"] = 0.08
    f["recent_bolus_volume"] = 0.0
    f["recent_carb_input"] = 0.0
    return f

# --- 1. Root & Documentation Endpoints ---
def test_root_index(client):
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["project"] == "GlycoTwin API"
    assert data["status"] == "operational"

def test_openapi_docs(client):
    res = client.get("/openapi.json")
    assert res.status_code == 200
    schema = res.json()
    assert "paths" in schema
    assert "/api/health" in schema["paths"]
    assert "/api/predictions" in schema["paths"]

# --- 2. Health & Metadata Endpoints ---
def test_get_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["dataset_accessible"] is True
    assert data["total_participants"] == 25
    assert data["total_observations"] == 309392
    assert "xgboost" in data["models_loaded"]

def test_get_metadata(client):
    res = client.get("/api/metadata")
    assert res.status_code == 200
    data = res.json()
    assert data["total_participants"] == 25
    assert data["feature_count"] == 28
    assert len(data["feature_names"]) == 28
    assert data["hypoglycemia_threshold_mgdl"] == 70.0
    assert "task_a_future_hypo" in data["available_tasks"]
    assert "task_b_impending_onset" in data["available_tasks"]

# --- 3. Patient Endpoints ---
def test_list_patients_default(client):
    res = client.get("/api/patients")
    assert res.status_code == 200
    data = res.json()
    assert len(data["patients"]) == 25
    assert data["pagination"]["total_items"] == 25
    assert data["pagination"]["page"] == 1

def test_list_patients_pagination(client):
    res = client.get("/api/patients?page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()
    assert len(data["patients"]) == 10
    assert data["pagination"]["total_pages"] == 3

def test_get_patient_detail_success(client):
    res = client.get("/api/patients/HUPA0001P")
    assert res.status_code == 200
    data = res.json()
    assert data["participant_id"] == "HUPA0001P"
    assert data["observation_count"] > 1000
    assert "glucose_stats" in data
    assert data["glucose_stats"]["mean"] > 50

def test_get_patient_detail_not_found(client):
    res = client.get("/api/patients/NONEXISTENT_ID")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"]

def test_get_patient_observations(client):
    res = client.get("/api/patients/HUPA0001P/observations?limit=25")
    assert res.status_code == 200
    data = res.json()
    assert data["participant_id"] == "HUPA0001P"
    assert len(data["observations"]) == 25
    assert data["observations"][0]["glucose"] > 0

def test_get_patient_observations_not_found(client):
    res = client.get("/api/patients/NONEXISTENT_ID/observations")
    assert res.status_code == 404

def test_get_patient_predictions(client):
    res = client.get("/api/patients/HUPA0001P/predictions?task=onset&model=xgboost&limit=15")
    assert res.status_code == 200
    data = res.json()
    assert data["participant_id"] == "HUPA0001P"
    assert len(data["predictions"]) == 15
    pred0 = data["predictions"][0]
    assert pred0["task"] == "task_b_impending_onset"
    assert pred0["model"] == "xgboost"
    assert 0.0 <= pred0["predicted_probability"] <= 1.0
    assert pred0["predicted_class"] in [0, 1]

# --- 4. Evaluation & Personalisation Endpoints ---
def test_get_evaluation_onset(client):
    res = client.get("/api/models/evaluation?task=onset")
    assert res.status_code == 200
    data = res.json()
    assert data["task"] == "task_b_impending_onset"
    assert len(data["models"]) == 3
    xgb = next(m for m in data["models"] if m["model"] == "xgboost")
    assert xgb["pooled_metrics"]["roc_auc"] > 0.90
    assert xgb["pooled_metrics"]["average_precision"] > 0.50

def test_get_evaluation_risk(client):
    res = client.get("/api/models/evaluation?task=risk")
    assert res.status_code == 200
    data = res.json()
    assert data["task"] == "task_a_future_hypo"
    assert len(data["models"]) == 3

def test_get_personalisation_all(client):
    res = client.get("/api/models/personalisation")
    assert res.status_code == 200
    data = res.json()
    assert data["total_participants"] == 25
    assert len(data["participants"]) == 25
    assert data["purge_gap_minutes"] == 30
    assert data["successful_adaptations"] == 24
    assert data["fallback_adaptations"] == 1
    assert data["summary_deltas"]["mean_delta_brier"] < 0

def test_get_personalisation_single_patient(client):
    res = client.get("/api/models/personalisation?participant_id=HUPA0001P")
    assert res.status_code == 200
    data = res.json()
    assert len(data["participants"]) == 1
    assert data["participants"][0]["participant_id"] == "HUPA0001P"
    assert data["participants"][0]["adaptation_status"] == "personalised"

def test_get_personalisation_unknown_patient(client):
    res = client.get("/api/models/personalisation?participant_id=NONEXISTENT")
    assert res.status_code == 404

# --- 5. Prediction Inference Endpoints ---
def test_inference_task_a_success(client, valid_features):
    payload = {
        "task": "risk",
        "model": "xgboost",
        "features": valid_features
    }
    res = client.post("/api/predictions", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["task"] == "task_a_future_hypo"
    assert data["model"] == "xgboost"
    assert 0.0 <= data["predicted_probability"] <= 1.0
    assert data["predicted_class"] in [0, 1]
    assert data["operational_threshold"] == 0.8707

def test_inference_task_b_success(client, valid_features):
    payload = {
        "task": "onset",
        "model": "xgboost",
        "features": valid_features
    }
    res = client.post("/api/predictions", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["task"] == "task_b_impending_onset"
    assert data["operational_threshold"] == 0.9148

def test_inference_task_b_condition_rejection(client, valid_features):
    f_low = dict(valid_features)
    f_low["glucose_current"] = 62.0  # Hypoglycemia violates Task B precondition
    payload = {
        "task": "onset",
        "model": "xgboost",
        "features": f_low
    }
    res = client.post("/api/predictions", json=payload)
    assert res.status_code == 422
    assert "conditionally on current glucose being >= 70.0" in res.json()["detail"]

def test_inference_missing_features(client, valid_features):
    f_inc = dict(valid_features)
    del f_inc["glucose_lag_5m"]
    payload = {
        "task": "risk",
        "model": "xgboost",
        "features": f_inc
    }
    res = client.post("/api/predictions", json=payload)
    assert res.status_code == 422
    assert "Missing required feature fields" in res.json()["detail"]

def test_inference_leakage_field(client, valid_features):
    f_leak = dict(valid_features)
    f_leak["future_min_glucose_30m"] = 55.0
    payload = {
        "task": "risk",
        "model": "xgboost",
        "features": f_leak
    }
    res = client.post("/api/predictions", json=payload)
    assert res.status_code == 422
    assert "Leakage violation" in res.json()["detail"]

# --- 7. Phase 5 Regression Tests ---
def test_personalisation_fallback_participant_identity(client):
    """
    Phase 5 Regression Test:
    Ensures that the personalisation fallback participant is strictly HUPA0009P (0 calibration positives),
    that nonexistent HUPA0012P is never present, and exactly 24 of 25 participants are successfully personalised.
    """
    res = client.get("/api/models/personalisation")
    assert res.status_code == 200
    data = res.json()
    
    participants = data["participants"]
    assert len(participants) == 25, f"Expected 25 participants, got {len(participants)}"
    
    p_ids = [p["participant_id"] for p in participants]
    assert "HUPA0012P" not in p_ids, "HUPA0012P is not in the HUPA-UCM cohort and must never be referenced"
    assert "HUPA0009P" in p_ids, "HUPA0009P must be present in personalisation participants"
    
    fallbacks = [p for p in participants if p["adaptation_status"] == "fallback_insufficient_events"]
    assert len(fallbacks) == 1, f"Expected exactly 1 fallback participant, got {len(fallbacks)}"
    
    fb = fallbacks[0]
    assert fb["participant_id"] == "HUPA0009P"
    assert fb["calib_positives"] == 0
    assert fb["t_pers"] == fb["t_pop"]
    assert fb["delta_f1"] is None or fb["delta_f1"] == 0.0
    
    personalised = [p for p in participants if p["adaptation_status"] == "personalised"]
    assert len(personalised) == 24

def test_evaluation_threshold_and_metrics_consistency(client):
    """
    Phase 5 Regression Test:
    Reconciles authoritative Phase 2 evaluation metrics and operational thresholds across tasks.
    Verifies that Task A and Task B metrics match the authoritative out-of-fold ground truth,
    and that positive_count + negative_count strictly equals sample_count.
    """
    # Task A
    res_a = client.get("/api/models/evaluation?task=task_a_all_risk")
    assert res_a.status_code == 200
    data_a = res_a.json()
    xgb_a = next(m for m in data_a["models"] if m["model"] == "xgboost")
    assert xgb_a["operational_threshold"] == 0.8707
    assert xgb_a["sample_count"] == 308942
    assert xgb_a["positive_count"] == 27661
    assert xgb_a["negative_count"] == 281281
    assert xgb_a["positive_count"] + xgb_a["negative_count"] == xgb_a["sample_count"]
    assert round(xgb_a["pooled_metrics"]["roc_auc"], 4) == 0.9882
    assert round(xgb_a["pooled_metrics"]["average_precision"], 4) == 0.9316
    assert round(xgb_a["pooled_metrics"]["brier_score"], 4) == 0.0381
    assert round(xgb_a["macro_metrics"]["macro_mean_roc_auc"], 4) == 0.9891

    # Task B
    res_b = client.get("/api/models/evaluation?task=task_b_impending_onset")
    assert res_b.status_code == 200
    data_b = res_b.json()
    xgb_b = next(m for m in data_b["models"] if m["model"] == "xgboost")
    assert xgb_b["operational_threshold"] == 0.9148
    assert xgb_b["sample_count"] == 288628
    assert xgb_b["positive_count"] == 8742
    assert xgb_b["negative_count"] == 279886
    assert xgb_b["positive_count"] + xgb_b["negative_count"] == xgb_b["sample_count"]
    assert round(xgb_b["pooled_metrics"]["roc_auc"], 4) == 0.9667
    assert round(xgb_b["pooled_metrics"]["average_precision"], 4) == 0.5843
    assert round(xgb_b["pooled_metrics"]["brier_score"], 4) == 0.0709
    assert round(xgb_b["macro_metrics"]["macro_mean_roc_auc"], 4) == 0.9711
    assert round(xgb_b["macro_metrics"]["macro_mean_average_precision"], 4) == 0.6325


