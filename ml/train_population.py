"""
GlycoTwin: Population Model Training & Participant-Aware Evaluation Module.
Executes leak-free GroupKFold cross-validation across participants for:
1. Rule-based Baseline
2. Regularized Logistic Regression
3. Gradient Boosted Trees (XGBoost)

Saves out-of-fold prediction matrices and serializes trained models.
"""
from typing import Dict, Any, List, Tuple
from pathlib import Path
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold
from xgboost import XGBClassifier

from ml.model_config import ExperimentConfig, DEFAULT_EXPERIMENT_CONFIG, TASK_A_TARGET, TASK_B_TARGET
from ml.train_baselines import RuleBasedHypoBaseline, build_logistic_regression_pipeline
from ml.metrics import find_optimal_threshold, compute_classification_metrics

def train_and_eval_population_models(
    df: pd.DataFrame,
    task_name: str,
    target_col: str,
    config: ExperimentConfig = DEFAULT_EXPERIMENT_CONFIG
) -> Tuple[pd.DataFrame, Dict[str, Any], Dict[str, Any]]:
    """
    Runs participant-grouped cross-validation for a specified prediction task.
    
    Inputs:
        - df: Full feature DataFrame with metadata.
        - task_name: "task_a_future_hypo" or "task_b_impending_onset"
        - target_col: Name of binary target column in df.
        - config: ExperimentConfig instance.
        
    Returns:
        - oof_predictions_df: DataFrame containing out-of-fold probabilities and predictions.
        - fold_thresholds: Dict of training-calibrated thresholds per model and fold.
        - fitted_final_models: Dict of models retrained on the full task dataset.
    """
    feature_cols = config.feature_columns
    
    # Filter dataset to task eligibility
    if task_name == "task_b_impending_onset":
        # Task B is conditional on current glucose >= 70 mg/dL (normoglycemic/hyperglycemic baseline)
        mask = df["is_modelling_eligible"] & (df["glucose_current"] >= 70.0) & df[target_col].notna()
    else:
        # Task A is unconditional over all eligible windows
        mask = df["is_modelling_eligible"] & df[target_col].notna()

    task_df = df[mask].copy().reset_index(drop=True)
    n_samples = len(task_df)
    n_participants = task_df["participant_id"].nunique()

    print(f"\n--- Running Population Evaluation: {task_name.upper()} ---")
    print(f"Target Column: {target_col}")
    print(f"Eligible Task Observations: {n_samples:,} across {n_participants} participants.")
    print(f"Positive Events: {(task_df[target_col] == 1).sum():,} ({task_df[target_col].mean()*100:.2f}%)")

    # GroupKFold by participant
    gkf = GroupKFold(n_splits=config.n_splits)
    groups = task_df["participant_id"].values
    X_all = task_df[feature_cols]
    y_all = task_df[target_col].values.astype(int)

    # Initialize out-of-fold prediction columns
    models = ["rule_based", "logistic_regression", "xgboost"]
    oof_probs = {m: np.zeros(n_samples, dtype=float) for m in models}
    oof_preds = {m: np.zeros(n_samples, dtype=int) for m in models}
    fold_assignment = np.zeros(n_samples, dtype=int)
    fold_thresholds = {m: [] for m in models}

    for fold_idx, (train_idx, val_idx) in enumerate(gkf.split(X_all, y_all, groups=groups)):
        train_pids = np.unique(groups[train_idx])
        val_pids = np.unique(groups[val_idx])
        fold_assignment[val_idx] = fold_idx + 1

        print(f"  Fold {fold_idx + 1}/{config.n_splits}: {len(train_pids)} train participants ({len(train_idx):,} rows) -> {len(val_pids)} val participants ({len(val_idx):,} rows)")

        X_train, y_train = X_all.iloc[train_idx], y_all[train_idx]
        X_val, y_val = X_all.iloc[val_idx], y_all[val_idx]

        # 1. Rule-Based Baseline
        rb_model = RuleBasedHypoBaseline()
        rb_model.fit(X_train, y_train)
        p_train_rb = rb_model.predict_proba(X_train)[:, 1]
        p_val_rb = rb_model.predict_proba(X_val)[:, 1]
        t_rb = find_optimal_threshold(y_train, p_train_rb, strategy=config.threshold_strategy)
        oof_probs["rule_based"][val_idx] = p_val_rb
        oof_preds["rule_based"][val_idx] = (p_val_rb >= t_rb).astype(int)
        fold_thresholds["rule_based"].append(t_rb)

        # 2. Logistic Regression Pipeline (StandardScaler + LogisticRegression)
        lr_model = build_logistic_regression_pipeline(
            C=config.logreg_params["C"],
            class_weight=config.logreg_params["class_weight"],
            random_state=config.random_seed
        )
        lr_model.fit(X_train, y_train)
        p_train_lr = lr_model.predict_proba(X_train)[:, 1]
        p_val_lr = lr_model.predict_proba(X_val)[:, 1]
        t_lr = find_optimal_threshold(y_train, p_train_lr, strategy=config.threshold_strategy)
        oof_probs["logistic_regression"][val_idx] = p_val_lr
        oof_preds["logistic_regression"][val_idx] = (p_val_lr >= t_lr).astype(int)
        fold_thresholds["logistic_regression"].append(t_lr)

        # 3. XGBoost
        # Calculate scale_pos_weight strictly on training split
        n_pos_train = (y_train == 1).sum()
        n_neg_train = (y_train == 0).sum()
        scale_pos = (n_neg_train / n_pos_train) if n_pos_train > 0 else 1.0

        xgb_params = dict(config.xgb_params)
        xgb_params["scale_pos_weight"] = scale_pos
        xgb_model = XGBClassifier(**xgb_params)
        xgb_model.fit(X_train, y_train)
        p_train_xgb = xgb_model.predict_proba(X_train)[:, 1]
        p_val_xgb = xgb_model.predict_proba(X_val)[:, 1]
        t_xgb = find_optimal_threshold(y_train, p_train_xgb, strategy=config.threshold_strategy)
        oof_probs["xgboost"][val_idx] = p_val_xgb
        oof_preds["xgboost"][val_idx] = (p_val_xgb >= t_xgb).astype(int)
        fold_thresholds["xgboost"].append(t_xgb)

    # Assemble prediction output DataFrame
    oof_df = task_df[["participant_id", "time", "source_file", "glucose_current"]].copy()
    oof_df["task_name"] = task_name
    oof_df["target_name"] = target_col
    oof_df["true_target"] = y_all
    oof_df["cv_fold"] = fold_assignment

    for m in models:
        oof_df[f"prob_{m}"] = np.round(oof_probs[m], 4)
        oof_df[f"pred_{m}"] = oof_preds[m]

    # Fit final models on full dataset for export/inference
    fitted_final_models = {}
    print(f"  Fitting final models on full {task_name} dataset for serialization...")

    # Final Logistic Regression
    final_lr = build_logistic_regression_pipeline(
        C=config.logreg_params["C"],
        class_weight=config.logreg_params["class_weight"],
        random_state=config.random_seed
    )
    final_lr.fit(X_all, y_all)
    fitted_final_models["logistic_regression"] = final_lr

    # Final XGBoost
    full_scale_pos = ((y_all == 0).sum() / (y_all == 1).sum()) if (y_all == 1).sum() > 0 else 1.0
    final_xgb_params = dict(config.xgb_params)
    final_xgb_params["scale_pos_weight"] = full_scale_pos
    final_xgb = XGBClassifier(**final_xgb_params)
    final_xgb.fit(X_all, y_all)
    fitted_final_models["xgboost"] = final_xgb

    return oof_df, fold_thresholds, fitted_final_models
