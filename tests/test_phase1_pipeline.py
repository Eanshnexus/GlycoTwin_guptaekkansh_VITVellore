"""
Unit & Integration Tests for Phase 1: Data Pipeline & Feature Engineering.
Validates loading, schema validation, preprocessing, causal feature generation,
leakage resistance, label creation, and artifact generation using synthetic fixtures.
"""
import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from ml.config import PipelineConfig
from ml.data_loader import (
    load_single_participant,
    discover_participant_files,
    load_all_participants,
    DataLoaderError,
    REQUIRED_COLUMNS
)
from ml.validate_data import validate_participant_data, validate_cohort
from ml.preprocess import preprocess_single_participant, preprocess_cohort
from ml.build_features import (
    compute_participant_features,
    build_feature_manifest,
    FEATURE_COLUMNS
)
from ml.create_labels import create_future_hypo_labels
from ml.run_pipeline import run_phase1_pipeline

@pytest.fixture
def synthetic_cgm_series():
    """Generates a small synthetic 24-hour 5-minute dataset (288 rows)."""
    n = 288
    times = pd.date_range("2024-01-01 00:00:00", periods=n, freq="5min")
    np.random.seed(42)
    # Sinusoid glucose curve around 130 mg/dL with known hypo dips below 70 at steps 40..45
    glucose = 130.0 + 30.0 * np.sin(np.linspace(0, 4 * np.pi, n))
    glucose[40:46] = [68.0, 64.0, 60.0, 58.0, 62.0, 67.0]

    df = pd.DataFrame({
        "time": times.strftime("%Y-%m-%dT%H:%M:%S"),
        "glucose": np.round(glucose, 1),
        "calories": np.random.uniform(1.0, 10.0, n),
        "heart_rate": np.random.uniform(65.0, 95.0, n),
        "steps": np.random.choice([0, 10, 40], n),
        "basal_rate": np.full(n, 0.08),
        "bolus_volume_delivered": np.zeros(n),
        "carb_input": np.zeros(n)
    })
    # Add a bolus and meal at step 30
    df.loc[30, "bolus_volume_delivered"] = 4.5
    df.loc[30, "carb_input"] = 45.0
    return df

@pytest.fixture
def synthetic_participant_file(tmp_path, synthetic_cgm_series):
    """Writes synthetic participant data to a temporary CSV file."""
    fpath = tmp_path / "HUPA0001P.csv"
    synthetic_cgm_series.to_csv(fpath, sep=";", index=False)
    return fpath

# --- TEST 1: Correct loading of valid participant file ---
def test_load_valid_participant(synthetic_participant_file):
    df = load_single_participant(synthetic_participant_file)
    assert len(df) == 288
    assert df["participant_id"].iloc[0] == "HUPA0001P"
    assert pd.api.types.is_datetime64_any_dtype(df["time"])
    for col in REQUIRED_COLUMNS:
        assert col in df.columns

# --- TEST 2: Missing required columns rejected ---
def test_missing_required_columns(tmp_path):
    bad_df = pd.DataFrame({
        "time": ["2024-01-01T00:00:00"],
        "glucose": [120.0]
        # Missing calories, heart_rate, steps, etc.
    })
    bad_path = tmp_path / "HUPA_bad.csv"
    bad_df.to_csv(bad_path, sep=";", index=False)
    with pytest.raises(DataLoaderError, match="missing required columns"):
        load_single_participant(bad_path)

# --- TEST 3: Invalid timestamps detected ---
def test_invalid_timestamps(tmp_path):
    bad_df = pd.DataFrame({
        "time": ["not-a-valid-timestamp"],
        "glucose": [120.0],
        "calories": [2.0],
        "heart_rate": [75.0],
        "steps": [0.0],
        "basal_rate": [0.08],
        "bolus_volume_delivered": [0.0],
        "carb_input": [0.0]
    })
    bad_path = tmp_path / "HUPA_bad_time.csv"
    bad_df.to_csv(bad_path, sep=";", index=False)
    with pytest.raises(DataLoaderError, match="Failed to parse 'time' column"):
        load_single_participant(bad_path)

# --- TEST 4: Duplicate timestamps detected and handled ---
def test_duplicate_timestamps_handling(synthetic_cgm_series):
    # Inject duplicate timestamp at index 10
    dup_series = synthetic_cgm_series.copy()
    dup_series.loc[11, "time"] = dup_series.loc[10, "time"]
    dup_series["participant_id"] = "TEST_DUP"

    # Validation detects error
    val = validate_participant_data(dup_series)
    assert val["duplicate_timestamps"] == 1
    assert any("duplicate timestamps" in err.lower() for err in val["errors"])

    # Preprocessing deduplicates conservatively (keeps first, excludes duplicate)
    clean_df, meta = preprocess_single_participant(dup_series)
    assert len(clean_df) == len(dup_series) - 1
    assert meta["exclusions_detail"]["duplicate_timestamps_excluded"] == 1

# --- TEST 5: Irregular sampling intervals detected ---
def test_irregular_sampling_intervals(synthetic_cgm_series):
    gapped = synthetic_cgm_series.copy()
    # Inject a 30-minute gap by dropping rows 20 to 24
    gapped = gapped.drop(index=list(range(20, 25))).reset_index(drop=True)
    gapped["participant_id"] = "TEST_GAP"

    val = validate_participant_data(gapped)
    assert val["gaps_gt_interval"] > 0
    assert val["max_gap_minutes"] == 30.0

# --- TEST 6: Participant boundary handling ---
def test_participant_boundary_handling(tmp_path, synthetic_cgm_series):
    p1 = tmp_path / "HUPA0001P.csv"
    p2 = tmp_path / "HUPA0002P.csv"
    synthetic_cgm_series.to_csv(p1, sep=";", index=False)
    synthetic_cgm_series.to_csv(p2, sep=";", index=False)

    cohort = load_all_participants(tmp_path)
    assert len(cohort) == 2
    assert "HUPA0001P" in cohort
    assert "HUPA0002P" in cohort
    # Confirm records are separate and not concatenated across boundary
    assert (cohort["HUPA0001P"]["participant_id"] == "HUPA0001P").all()
    assert (cohort["HUPA0002P"]["participant_id"] == "HUPA0002P").all()

# --- TEST 7: Correct 5m, 10m, 15m, 30m, 60m lags ---
def test_lag_feature_calculations(synthetic_cgm_series):
    synthetic_cgm_series["participant_id"] = "TEST_LAGS"
    synthetic_cgm_series["time"] = pd.to_datetime(synthetic_cgm_series["time"])
    feats = compute_participant_features(synthetic_cgm_series)

    # For index 20:
    # lag 5m is index 19, lag 10m is 18, lag 15m is 17, lag 30m is 14, lag 60m is 8
    g = synthetic_cgm_series["glucose"]
    idx = 20
    assert feats.loc[idx, "glucose_lag_5m"] == g.iloc[idx - 1]
    assert feats.loc[idx, "glucose_lag_10m"] == g.iloc[idx - 2]
    assert feats.loc[idx, "glucose_lag_15m"] == g.iloc[idx - 3]
    assert feats.loc[idx, "glucose_lag_30m"] == g.iloc[idx - 6]
    assert feats.loc[idx, "glucose_lag_60m"] == g.iloc[idx - 12]

# --- TEST 8: Correct rolling-window calculations ---
def test_rolling_window_calculations(synthetic_cgm_series):
    synthetic_cgm_series["participant_id"] = "TEST_ROLL"
    synthetic_cgm_series["time"] = pd.to_datetime(synthetic_cgm_series["time"])
    feats = compute_participant_features(synthetic_cgm_series)

    g = synthetic_cgm_series["glucose"]
    idx = 30
    # Mean 15m is past 3 steps (idx-2, idx-1, idx)
    expected_mean_15m = g.iloc[idx - 2 : idx + 1].mean()
    assert np.isclose(feats.loc[idx, "glucose_mean_15m"], expected_mean_15m)

    # Min 30m is past 6 steps
    expected_min_30m = g.iloc[idx - 5 : idx + 1].min()
    assert np.isclose(feats.loc[idx, "glucose_min_30m"], expected_min_30m)

# --- TEST 9: Correct time-of-day circadian features ---
def test_time_of_day_features():
    df = pd.DataFrame({
        "time": pd.to_datetime(["2024-01-01 00:00:00", "2024-01-01 06:00:00", "2024-01-01 12:00:00", "2024-01-01 18:00:00"]),
        "glucose": [100.0, 105.0, 110.0, 115.0],
        "participant_id": "TEST_TIME"
    })
    feats = compute_participant_features(df)
    # At 00:00, sin(0) = 0, cos(0) = 1
    assert np.isclose(feats.loc[0, "hour_sin"], 0.0, atol=1e-5)
    assert np.isclose(feats.loc[0, "hour_cos"], 1.0, atol=1e-5)
    # At 06:00 (quarter day), sin(pi/2) = 1, cos(pi/2) = 0
    assert np.isclose(feats.loc[1, "hour_sin"], 1.0, atol=1e-5)
    assert np.isclose(feats.loc[1, "hour_cos"], 0.0, atol=1e-5)

# --- TEST 10: Correct future-event labels ---
def test_future_event_labels(synthetic_cgm_series):
    synthetic_cgm_series["time"] = pd.to_datetime(synthetic_cgm_series["time"])
    labels = create_future_hypo_labels(synthetic_cgm_series, threshold=70.0, horizon_minutes=30)

    # Hypo was injected at indices 40..45.
    # At index 35, the next 6 steps are 36..41 (contains step 40 which is 68.0 < 70).
    # Therefore, index 35 MUST be positive (target_hypo_30m == 1)
    assert labels.loc[35, "target_hypo_30m"] == 1
    assert labels.loc[35, "target_eligible"] == True

    # At index 10, glucose is ~140 with no hypo in next 6 steps. Must be negative (0)
    assert labels.loc[10, "target_hypo_30m"] == 0
    assert labels.loc[10, "target_eligible"] == True

# --- TEST 11: Exclusion of incomplete future horizons ---
def test_incomplete_future_horizon_exclusion(synthetic_cgm_series):
    synthetic_cgm_series["time"] = pd.to_datetime(synthetic_cgm_series["time"])
    labels = create_future_hypo_labels(synthetic_cgm_series, horizon_minutes=30, expected_interval_minutes=5)
    n = len(synthetic_cgm_series)

    # The last 6 steps cannot observe a full 30-minute forward horizon.
    # They must have target_eligible == False and target_hypo_30m == NaN, NEVER 0!
    for idx in range(n - 6, n):
        assert labels.loc[idx, "target_eligible"] == False
        assert np.isnan(labels.loc[idx, "target_hypo_30m"])

# --- TEST 12: NO FUTURE-DATA LEAKAGE IN FEATURES ---
def test_leakage_resistance_future_alteration(synthetic_cgm_series):
    """
    CRITICAL LEAKAGE TEST:
    Modifying future glucose observations at t > t0 must have ZERO impact
    on any feature computed at or before t0.
    """
    df1 = synthetic_cgm_series.copy()
    df2 = synthetic_cgm_series.copy()

    df1["time"] = pd.to_datetime(df1["time"])
    df2["time"] = pd.to_datetime(df2["time"])
    df1["participant_id"] = "TEST_LEAK"
    df2["participant_id"] = "TEST_LEAK"

    t0 = 50
    # Dramatically alter all future glucose readings after t0 in df2
    df2.loc[t0 + 1 :, "glucose"] = 399.0
    df2.loc[t0 + 1 :, "heart_rate"] = 180.0
    df2.loc[t0 + 1 :, "steps"] = 500.0

    feats1 = compute_participant_features(df1)
    feats2 = compute_participant_features(df2)

    # Check all feature columns up to t0
    for col in FEATURE_COLUMNS:
        v1 = feats1.loc[:t0, col].values
        v2 = feats2.loc[:t0, col].values
        # Handle NaNs during warmup
        np.testing.assert_allclose(
            np.nan_to_num(v1),
            np.nan_to_num(v2),
            err_msg=f"Future data leakage detected in feature '{col}' before prediction time t0!"
        )

# --- TEST 13: NO CROSS-PARTICIPANT LEAKAGE ---
def test_no_cross_participant_leakage(synthetic_cgm_series):
    """Labels and features must be computed strictly per-participant without bleed across IDs."""
    df1 = synthetic_cgm_series.copy()
    df2 = synthetic_cgm_series.copy()
    df1["participant_id"] = "P1"
    df2["participant_id"] = "P2"
    df1["time"] = pd.to_datetime(df1["time"])
    df2["time"] = pd.to_datetime(df2["time"])

    # P1 has hypo at 40..45, P2 has completely normal glucose everywhere
    df2["glucose"] = 120.0

    labels1 = create_future_hypo_labels(df1)
    labels2 = create_future_hypo_labels(df2)

    assert (labels1["target_hypo_30m"] == 1).sum() > 0
    assert (labels2["target_hypo_30m"] == 1).sum() == 0  # Zero positive labels for P2

# --- TEST 14: Handling of missing contextual variables ---
def test_missing_contextual_variables(synthetic_cgm_series):
    minimal = synthetic_cgm_series[["time", "glucose"]].copy()
    minimal["time"] = pd.to_datetime(minimal["time"])
    minimal["participant_id"] = "MINIMAL"

    # Should gracefully default missing contextual fields to 0.0 without crashing
    feats = compute_participant_features(minimal)
    assert "recent_steps" in feats.columns
    assert (feats["recent_steps"] == 0.0).all()
    assert (feats["recent_bolus_volume"] == 0.0).all()

# --- TEST 15: Stable output schema ---
def test_stable_output_schema():
    manifest = build_feature_manifest()
    assert manifest["total_features"] == len(FEATURE_COLUMNS)
    for col in FEATURE_COLUMNS:
        assert col in manifest["features"]
        assert "lookback_minutes" in manifest["features"][col]
        assert "units" in manifest["features"][col]

# --- TEST 16: Pipeline reproducibility on identical input ---
def test_pipeline_reproducibility(tmp_path, synthetic_cgm_series):
    prep_dir = tmp_path / "Preprocessed"
    prep_dir.mkdir()
    synthetic_cgm_series.to_csv(prep_dir / "HUPA0001P.csv", sep=";", index=False)

    out1 = tmp_path / "out1"
    out2 = tmp_path / "out2"
    art1 = tmp_path / "art1"
    art2 = tmp_path / "art2"

    cfg1 = PipelineConfig(dataset_dir=tmp_path, output_dir=out1, artifacts_dir=art1)
    cfg2 = PipelineConfig(dataset_dir=tmp_path, output_dir=out2, artifacts_dir=art2)

    res1 = run_phase1_pipeline(cfg1, save_csv=True)
    res2 = run_phase1_pipeline(cfg2, save_csv=True)

    assert res1["total_modelling_eligible_windows"] == res2["total_modelling_eligible_windows"]
    assert res1["positive_labels_count"] == res2["positive_labels_count"]
    assert res1["negative_labels_count"] == res2["negative_labels_count"]

# --- TEST 17: Pipeline behaviour when no valid windows remain ---
def test_empty_windows_handling():
    short_df = pd.DataFrame({
        "time": pd.date_range("2024-01-01", periods=3, freq="5min"),
        "glucose": [120.0, 125.0, 130.0],
        "participant_id": "SHORT"
    })
    labels = create_future_hypo_labels(short_df, horizon_minutes=30)
    # With only 3 observations, no 6-step forward window can exist
    assert (labels["target_eligible"] == False).all()

# --- TEST 18: Feature manifests and summary reports generated ---
def test_manifest_and_summary_generation(tmp_path, synthetic_cgm_series):
    prep_dir = tmp_path / "Preprocessed"
    prep_dir.mkdir()
    synthetic_cgm_series.to_csv(prep_dir / "HUPA0001P.csv", sep=";", index=False)

    cfg = PipelineConfig(dataset_dir=tmp_path, output_dir=tmp_path / "out", artifacts_dir=tmp_path / "art")
    run_phase1_pipeline(cfg, save_csv=True)

    manifest_file = tmp_path / "art" / "phase1_feature_manifest.json"
    summary_file = tmp_path / "art" / "phase1_pipeline_summary.json"
    assert manifest_file.exists()
    assert summary_file.exists()
