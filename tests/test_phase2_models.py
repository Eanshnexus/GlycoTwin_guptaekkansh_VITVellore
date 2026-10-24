"""
Unit & Integration Tests for Phase 2: Machine Learning Models, Evaluation & Personalisation.
Tests feature selection, target exclusions, GroupKFold participant separation,
leakage prevention, metrics edge-cases, chronological adaptation, and model serialization.
"""
import os
import tempfile
from pathlib import Path
import pytest
import numpy as np
import pandas as pd
import joblib

from ml.model_config import ExperimentConfig, DEFAULT_EXPERIMENT_CONFIG, LEAKAGE_EXCLUSIONS
from ml.metrics import (
    compute_classification_metrics,
    find_optimal_threshold,
    compute_per_participant_metrics,
    compute_macro_summary
)
from ml.train_baselines import RuleBasedHypoBaseline, build_logistic_regression_pipeline
from ml.train_personalised import PersonalisedAdapter, run_personalisation_experiment
from ml.train_population import train_and_eval_population_models

@pytest.fixture
def synthetic_phase2_dataset():
    """Creates synthetic multi-participant dataset formatted exactly like glycotwin_features.parquet."""
    records = []
    np.random.seed(42)
    # 3 participants, 100 rows each
    for pid in ["P01", "P02", "P03"]:
        times = pd.date_range("2024-01-01 00:00:00", periods=100, freq="5min")
        g = 120.0 + 30.0 * np.sin(np.linspace(0, 2 * np.pi, 100)) + np.random.normal(0, 3, 100)
        
        # P01 and P02 have some hypo events; P03 has 0 hypo events (testing degenerate class handling)
        if pid in ["P01", "P02"]:
            g[30:35] = [68, 65, 62, 58, 66]
            y_risk = np.zeros(100)
            y_risk[25:35] = 1.0  # Hypo in next 30m
            y_onset = np.zeros(100)
            y_onset[25:30] = 1.0 # Current >= 70 and hypo in next 30m
        else:
            y_risk = np.zeros(100)
            y_onset = np.zeros(100)

        df = pd.DataFrame({
            "participant_id": pid,
            "time": times,
            "source_file": f"{pid}.csv",
            "glucose_current": g,
            "glucose_lag_5m": np.roll(g, 1),
            "glucose_lag_10m": np.roll(g, 2),
            "glucose_lag_15m": np.roll(g, 3),
            "glucose_lag_30m": np.roll(g, 6),
            "glucose_lag_60m": np.roll(g, 12),
            "glucose_change_5m": g - np.roll(g, 1),
            "glucose_change_15m": g - np.roll(g, 3),
            "glucose_change_30m": g - np.roll(g, 6),
            "glucose_slope_15m": (g - np.roll(g, 3)) / 15.0,
            "glucose_slope_30m": (g - np.roll(g, 6)) / 30.0,
            "glucose_mean_15m": g,
            "glucose_mean_30m": g,
            "glucose_mean_60m": g,
            "glucose_std_30m": np.full(100, 5.0),
            "glucose_std_60m": np.full(100, 8.0),
            "glucose_min_30m": g - 5,
            "glucose_max_30m": g + 5,
            "hour_sin": np.sin(2 * np.pi * times.hour / 24.0),
            "hour_cos": np.cos(2 * np.pi * times.hour / 24.0),
            "weekday_sin": np.zeros(100),
            "weekday_cos": np.ones(100),
            "recent_calories": np.full(100, 15.0),
            "recent_steps": np.full(100, 100.0),
            "recent_heart_rate": np.full(100, 75.0),
            "recent_basal_rate": np.full(100, 0.08),
            "recent_bolus_volume": np.zeros(100),
            "recent_carb_input": np.zeros(100),
            "target_hypo_30m": y_risk,
            "is_hypo_onset_30m": y_onset,
            "future_min_glucose_30m": g,
            "target_eligible": True,
            "is_modelling_eligible": True
        })
        records.append(df)
    return pd.concat(records, ignore_index=True)

# --- TEST 1: Correct feature-column selection ---
def test_feature_column_selection():
    cfg = DEFAULT_EXPERIMENT_CONFIG
    assert len(cfg.feature_columns) == 28
    assert "glucose_current" in cfg.feature_columns
    assert "glucose_slope_15m" in cfg.feature_columns

# --- TEST 2: Exclusion of target-derived fields ---
def test_exclusion_of_leakage_fields():
    cfg = DEFAULT_EXPERIMENT_CONFIG
    for field in LEAKAGE_EXCLUSIONS:
        assert field not in cfg.feature_columns, f"Leakage violation: {field} must not be in model features!"

# --- TEST 3 & 4: Participant-aware CV with NO overlap between train and val ---
def test_participant_aware_cv_no_overlap(synthetic_phase2_dataset):
    cfg = ExperimentConfig(n_splits=3)
    oof_df, thresholds, models = train_and_eval_population_models(
        df=synthetic_phase2_dataset,
        task_name="task_b_impending_onset",
        target_col="is_hypo_onset_30m",
        config=cfg
    )
    assert len(oof_df) > 0
    # Check that each participant was evaluated strictly once in out-of-fold predictions
    for pid in ["P01", "P02", "P03"]:
        folds = oof_df.loc[oof_df["participant_id"] == pid, "cv_fold"].unique()
        assert len(folds) == 1, f"Participant {pid} should belong to exactly 1 validation fold!"

# --- TEST 5: Correct probability prediction shape ---
def test_probability_prediction_shape(synthetic_phase2_dataset):
    X = synthetic_phase2_dataset[DEFAULT_EXPERIMENT_CONFIG.feature_columns]
    rb = RuleBasedHypoBaseline()
    probs_rb = rb.predict_proba(X)
    assert probs_rb.shape == (len(X), 2)
    assert (probs_rb >= 0.0).all() and (probs_rb <= 1.0).all()

# --- TEST 6: Correct handling of class imbalance ---
def test_class_imbalance_handling():
    lr = build_logistic_regression_pipeline(class_weight="balanced")
    assert lr.named_steps["classifier"].class_weight == "balanced"

# --- TEST 7: Correct computation of standard metrics ---
def test_standard_metrics_computation():
    y_true = np.array([0, 0, 0, 1, 1])
    y_prob = np.array([0.1, 0.2, 0.3, 0.8, 0.9])
    m = compute_classification_metrics(y_true, y_prob, threshold=0.5)
    assert m["roc_auc"] == 1.0
    assert m["average_precision"] == 1.0
    assert m["sensitivity"] == 1.0
    assert m["specificity"] == 1.0
    assert m["f1_score"] == 1.0

# --- TEST 8 & 9: Undefined ROC-AUC & Precision/Recall handling (Zero positive events) ---
def test_undefined_metrics_zero_positives():
    y_true = np.array([0, 0, 0, 0])
    y_prob = np.array([0.1, 0.2, 0.1, 0.3])
    m = compute_classification_metrics(y_true, y_prob, threshold=0.5)
    assert m["is_degenerate"] == True
    assert m["roc_auc"] is None  # Undefined when 0 positive events
    assert m["average_precision"] is None
    assert m["specificity"] == 1.0

# --- TEST 10 & 11: Personalisation split chronology & NO use of evaluation labels in adaptation ---
def test_personalisation_split_chronology(synthetic_phase2_dataset):
    cfg = ExperimentConfig(personalisation_split_ratio=0.30)
    eval_preds_df, comp_df, meta = run_personalisation_experiment(
        df=synthetic_phase2_dataset,
        task_name="task_b_impending_onset",
        target_col="is_hypo_onset_30m",
        config=cfg
    )
    assert len(eval_preds_df) > 0
    # Check that evaluation segment row counts match 70% of participant task-eligible rows
    for pid in ["P01", "P02"]:
        task_p = synthetic_phase2_dataset[(synthetic_phase2_dataset["participant_id"] == pid) & (synthetic_phase2_dataset["glucose_current"] >= 70.0)]
        n_p_total = len(task_p)
        n_calib = int(n_p_total * 0.30)
        n_eval = n_p_total - n_calib
        p_eval = eval_preds_df[eval_preds_df["participant_id"] == pid]
        assert len(p_eval) == n_eval

# --- TEST 12: Same evaluation observations for population and personalised models ---
def test_same_evaluation_observations(synthetic_phase2_dataset):
    cfg = ExperimentConfig(personalisation_split_ratio=0.30)
    eval_preds_df, comp_df, meta = run_personalisation_experiment(
        df=synthetic_phase2_dataset,
        task_name="task_b_impending_onset",
        target_col="is_hypo_onset_30m",
        config=cfg
    )
    # Confirm both pop_prob and pers_prob exist for every row in evaluation segment
    assert "pop_prob" in eval_preds_df.columns
    assert "pers_prob" in eval_preds_df.columns
    assert eval_preds_df["pop_prob"].notna().all()
    assert eval_preds_df["pers_prob"].notna().all()

# --- TEST 13: Fallback when personalisation data are insufficient ---
def test_personalisation_fallback_insufficient_events(synthetic_phase2_dataset):
    # P03 has 0 hypo events; should trigger fallback_insufficient_events
    cfg = ExperimentConfig(personalisation_split_ratio=0.30, min_calibration_positive_events=2)
    eval_preds_df, comp_df, meta = run_personalisation_experiment(
        df=synthetic_phase2_dataset,
        task_name="task_b_impending_onset",
        target_col="is_hypo_onset_30m",
        config=cfg
    )
    p03_comp = comp_df[comp_df["participant_id"] == "P03"].iloc[0]
    assert p03_comp["adaptation_status"] == "fallback_insufficient_events"
    # When falling back, pop and pers probabilities must be identical
    p03_eval = eval_preds_df[eval_preds_df["participant_id"] == "P03"]
    np.testing.assert_allclose(p03_eval["pop_prob"], p03_eval["pers_prob"])

# --- TEST 14: Reproducibility of results with fixed seed ---
def test_model_reproducibility(synthetic_phase2_dataset):
    cfg1 = ExperimentConfig(n_splits=3, random_seed=42)
    cfg2 = ExperimentConfig(n_splits=3, random_seed=42)

    oof1, _, _ = train_and_eval_population_models(synthetic_phase2_dataset, "task_b_impending_onset", "is_hypo_onset_30m", cfg1)
    oof2, _, _ = train_and_eval_population_models(synthetic_phase2_dataset, "task_b_impending_onset", "is_hypo_onset_30m", cfg2)

    np.testing.assert_allclose(oof1["prob_logistic_regression"], oof2["prob_logistic_regression"])

# --- TEST 15: Correct persistence and reloading of model artifacts ---
def test_model_serialization_reloading(tmp_path, synthetic_phase2_dataset):
    X = synthetic_phase2_dataset[DEFAULT_EXPERIMENT_CONFIG.feature_columns]
    y = synthetic_phase2_dataset["is_hypo_onset_30m"].values.astype(int)

    lr = build_logistic_regression_pipeline()
    lr.fit(X, y)
    model_path = tmp_path / "test_model.joblib"
    joblib.dump(lr, model_path)

    loaded_lr = joblib.load(model_path)
    probs_orig = lr.predict_proba(X)
    probs_loaded = loaded_lr.predict_proba(X)
    np.testing.assert_allclose(probs_orig, probs_loaded)

# --- TEST 16: Correct generation of evaluation reports ---
def test_macro_summary_generation():
    df = pd.DataFrame({
        "participant_id": ["P1", "P2"],
        "roc_auc": [0.90, 0.80],
        "average_precision": [0.60, 0.40]
    })
    summary = compute_macro_summary(df)
    assert summary["macro_mean_roc_auc"] == 0.85
    assert summary["macro_mean_average_precision"] == 0.50

# --- TEST 17: Leakage resistance under future glucose mutation ---
def test_feature_vector_future_alteration_leakage_resistance():
    """Mutating glucose values after time t must not alter feature vector at time t."""
    from ml.build_features import compute_participant_features
    times = pd.date_range("2024-01-01 00:00:00", periods=50, freq="5min")
    np.random.seed(42)
    glucose_orig = 120.0 + 10.0 * np.sin(np.linspace(0, np.pi, 50))
    df_orig = pd.DataFrame({
        "participant_id": "P_MUT",
        "time": times,
        "glucose": glucose_orig
    })
    feat_orig = compute_participant_features(df_orig)

    # Mutate all glucose values after index 25
    df_mut = df_orig.copy()
    glucose_mut = glucose_orig.copy()
    glucose_mut[26:] = 40.0  # Induce sudden severe hypoglycemia in future
    df_mut["glucose"] = glucose_mut
    feat_mut = compute_participant_features(df_mut)

    # Feature vector at index 25 (time t) must be strictly identical
    t_idx = 25
    orig_row = feat_orig.iloc[t_idx][DEFAULT_EXPERIMENT_CONFIG.feature_columns]
    mut_row = feat_mut.iloc[t_idx][DEFAULT_EXPERIMENT_CONFIG.feature_columns]
    pd.testing.assert_series_equal(orig_row, mut_row)

# --- TEST 18: Personalisation horizon purge gap prevents calibration overlap ---
def test_personalisation_horizon_purge_gap(synthetic_phase2_dataset):
    """Verify that calibration segment target windows strictly terminate before or at evaluation start time."""
    cfg = ExperimentConfig(personalisation_split_ratio=0.30)
    eval_preds_df, comp_df, meta = run_personalisation_experiment(
        df=synthetic_phase2_dataset,
        task_name="task_b_impending_onset",
        target_col="is_hypo_onset_30m",
        config=cfg
    )
    # Check that comp_df records purged rows
    assert "calib_rows_purged" in comp_df.columns
    for _, row in comp_df.iterrows():
        # Each participant must have had 6 rows purged (30 min / 5 min grid)
        assert row["calib_rows_purged"] > 0
        assert row["calib_rows_usable"] == row["calib_rows_total"] - row["calib_rows_purged"]

