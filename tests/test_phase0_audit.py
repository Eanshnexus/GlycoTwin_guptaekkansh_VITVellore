"""
Unit tests for Phase 0: Data Audit and Schema Verification.
Uses both synthetic fixture data for reproducibility and validates against the real local dataset when present.
"""
import os
import tempfile
import pandas as pd
import numpy as np
import pytest

from ml.audit import run_audit

@pytest.fixture
def synthetic_participant_data(tmp_path):
    """Generates synthetic 5-minute CGM data mimicking HUPA-UCM format for unit testing."""
    n_steps = 288  # 24 hours of 5-minute intervals
    times = pd.date_range("2024-01-01 00:00:00", periods=n_steps, freq="5min")
    np.random.seed(42)
    # Sinusoidal glucose curve with some dips below 70
    glucose = 120 + 40 * np.sin(np.linspace(0, 4 * np.pi, n_steps)) + np.random.normal(0, 5, n_steps)
    # Inject a known hypo episode (<70) between step 50 and 55
    glucose[50:56] = [68, 65, 62, 59, 64, 69]
    
    df = pd.DataFrame({
        "time": times.strftime("%Y-%m-%dT%H:%M:%S"),
        "glucose": np.round(glucose, 1),
        "calories": np.random.uniform(1.0, 15.0, n_steps),
        "heart_rate": np.random.uniform(60.0, 110.0, n_steps),
        "steps": np.random.choice([0, 10, 50, 120], n_steps),
        "basal_rate": np.full(n_steps, 0.08),
        "bolus_volume_delivered": np.zeros(n_steps),
        "carb_input": np.zeros(n_steps)
    })
    
    file_path = tmp_path / "HUPA0001P.csv"
    df.to_csv(file_path, sep=";", index=False)
    return str(tmp_path)

def test_synthetic_audit_loading_and_metrics(synthetic_participant_data):
    """Verifies that the audit correctly parses timestamps, rows, and detects hypoglycemia."""
    df = run_audit(synthetic_participant_data)
    assert len(df) == 1
    row = df.iloc[0]
    assert row["participant_id"] == "HUPA0001P"
    assert row["rows"] == 288
    assert row["pct_5min_intervals"] == 100.0
    assert row["gaps_gt_5min"] == 0
    assert row["time_hypo_pct"] > 0
    assert row["future_30m_hypo_all_count"] > 0
    # Check that null_counts dictionary has 0 for all columns
    for col, null_c in row["null_counts"].items():
        assert null_c == 0

def test_local_dataset_audit_when_available():
    """If the real HUPA-UCM dataset directory is present, verify all 25 participants are valid."""
    real_prep_dir = r"c:\Users\gupta\Desktop\GlycoTwin\HUPA-UCM Diabetes Dataset\HUPA-UCM Diabetes Dataset\Preprocessed"
    if not os.path.exists(real_prep_dir):
        pytest.skip("Real dataset directory not found, skipping real data test.")
    
    df = run_audit(real_prep_dir)
    assert len(df) == 25
    assert df["rows"].sum() == 309392
    assert (df["pct_5min_intervals"] == 100.0).all()
    assert (df["gaps_gt_5min"] == 0).all()
    assert (df["glucose_min"] > 0).all()
    assert (df["glucose_max"] < 1000).all()
    assert df["future_30m_hypo_onset_count"].sum() > 0
