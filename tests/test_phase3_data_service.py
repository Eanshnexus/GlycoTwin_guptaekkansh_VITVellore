"""
Unit Tests for Phase 3 DataService.
Tests data caching, patient summaries, observation pagination, and out-of-fold prediction retrieval.
"""
import pytest
from datetime import datetime
from backend.app.services.data_service import DataService

@pytest.fixture(scope="module")
def data_service():
    ds = DataService()
    ds.initialize()
    return ds

def test_data_service_initialization(data_service):
    assert data_service.is_ready is True
    assert data_service.total_participants == 25
    assert data_service.total_observations == 309392

def test_get_patient_ids(data_service):
    pids = data_service.get_patient_ids()
    assert len(pids) == 25
    assert "HUPA0001P" in pids
    assert "HUPA0025P" in pids

def test_get_patients_list_pagination(data_service):
    # Page 1, size 10
    items, total = data_service.get_patients_list(page=1, page_size=10)
    assert total == 25
    assert len(items) == 10
    assert items[0]["participant_id"] == "HUPA0001P"

    # Page 3, size 10 (should have remaining 5)
    items_p3, _ = data_service.get_patients_list(page=3, page_size=10)
    assert len(items_p3) == 5

def test_get_patient_detail(data_service):
    detail = data_service.get_patient_detail("HUPA0001P")
    assert detail is not None
    assert detail["participant_id"] == "HUPA0001P"
    assert detail["observation_count"] > 1000
    assert "glucose_stats" in detail
    stats = detail["glucose_stats"]
    assert stats["min"] > 0
    assert stats["max"] > stats["min"]
    assert 0 <= stats["tir_percentage"] <= 100
    assert detail["has_historical_predictions"] is True

def test_get_patient_detail_unknown(data_service):
    detail = data_service.get_patient_detail("UNKNOWN_PID")
    assert detail is None

def test_get_patient_observations_chronological(data_service):
    records, total = data_service.get_patient_observations("HUPA0001P", limit=50, offset=0)
    assert total > 1000
    assert len(records) == 50

    # Verify chronological ordering
    timestamps = [datetime.fromisoformat(r["time"]) for r in records]
    assert timestamps == sorted(timestamps)

    # Verify expected fields
    r0 = records[0]
    assert "glucose" in r0
    assert r0["glucose"] > 0
    assert "calories" in r0
    assert "steps" in r0
    assert "heart_rate" in r0
    assert "basal_rate" in r0

def test_get_patient_observations_date_filtering(data_service):
    detail = data_service.get_patient_detail("HUPA0001P")
    start = detail["start_time"]
    records, total = data_service.get_patient_observations(
        "HUPA0001P",
        start_time=start,
        end_time=start,
        limit=10,
        offset=0
    )
    assert len(records) >= 1
    assert records[0]["time"] == start

def test_get_patient_predictions(data_service):
    records, total = data_service.get_patient_predictions(
        patient_id="HUPA0001P",
        task="onset",
        model="xgboost",
        limit=20,
        offset=0
    )
    assert total > 0
    assert len(records) == 20
    r0 = records[0]
    assert r0["task"] == "task_b_impending_onset"
    assert r0["model"] == "xgboost"
    assert 0.0 <= r0["predicted_probability"] <= 1.0
    assert r0["predicted_class"] in [0, 1]
    assert r0["evaluation_type"] == "out_of_fold_cross_validation"
