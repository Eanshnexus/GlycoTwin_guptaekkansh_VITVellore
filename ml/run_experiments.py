"""
GlycoTwin: Phase 2 Master Experiment Execution CLI.
Executes reproducible training, cross-validation, personalisation,
metrics computation, and visualization generation.

Usage:
    python -m ml.run_experiments [--n-splits INT] [--random-seed INT]
"""
import os
import sys
import argparse
import json
import time
from pathlib import Path
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple

from ml.model_config import ExperimentConfig, DEFAULT_EXPERIMENT_CONFIG, TASK_A_TARGET, TASK_B_TARGET
from ml.train_population import train_and_eval_population_models
from ml.train_personalised import run_personalisation_experiment
from ml.metrics import compute_classification_metrics, compute_per_participant_metrics, compute_macro_summary
from ml.evaluate import perform_error_analysis, generate_evaluation_figures

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run GlycoTwin Phase 2 Machine Learning Experiments")
    parser.add_argument("--n-splits", type=int, default=5, help="Number of GroupKFold splits across participants")
    parser.add_argument("--random-seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--personalisation-ratio", type=float, default=0.30, help="Fraction of participant timeline used for calibration")
    return parser.parse_args()

def run_phase2_experiments(config: ExperimentConfig = DEFAULT_EXPERIMENT_CONFIG) -> Dict[str, Any]:
    start_time = time.time()
    print("=" * 75)
    print("GLYCOTWIN PHASE 2: BASELINE ML, EVALUATION & PERSONALISATION")
    print("=" * 75)

    data_path = config.workspace_root / config.data_parquet_path
    if not data_path.exists():
        raise FileNotFoundError(f"Modelling dataset not found at {data_path}. Please execute Phase 1 first.")

    eval_dir = config.workspace_root / config.evaluation_dir
    models_dir = config.workspace_root / config.models_dir
    eval_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading modeling dataset: {data_path}")
    df = pd.read_parquet(data_path)
    print(f"Loaded {len(df):,} observations across {df['participant_id'].nunique()} participants.")

    # ----------------------------------------------------
    # 1. TASK A: Population Evaluation (Hypo Risk in 30m)
    # ----------------------------------------------------
    oof_a_df, thresholds_a, models_a = train_and_eval_population_models(
        df=df,
        task_name="task_a_future_hypo",
        target_col=TASK_A_TARGET,
        config=config
    )

    # ----------------------------------------------------
    # 2. TASK B: Population Evaluation (Impending Onset in 30m)
    # ----------------------------------------------------
    oof_b_df, thresholds_b, models_b = train_and_eval_population_models(
        df=df,
        task_name="task_b_impending_onset",
        target_col=TASK_B_TARGET,
        config=config
    )

    # Combine OOF predictions
    combined_oof = pd.concat([oof_a_df, oof_b_df], ignore_index=True)
    oof_parquet_path = eval_dir / "population_oof_predictions.parquet"
    combined_oof.to_parquet(oof_parquet_path, index=False)
    print(f"\nSaved out-of-fold population predictions to: {oof_parquet_path}")

    # ----------------------------------------------------
    # 3. TASK B: Personalisation Experiment
    # ----------------------------------------------------
    pers_preds_df, pers_comparison_df, pers_meta = run_personalisation_experiment(
        df=df,
        task_name="task_b_impending_onset",
        target_col=TASK_B_TARGET,
        config=config
    )
    pers_parquet_path = eval_dir / "personalisation_predictions.parquet"
    pers_preds_df.to_parquet(pers_parquet_path, index=False)
    print(f"Saved personalisation predictions to: {pers_parquet_path}")

    # ----------------------------------------------------
    # 4. Metrics & Comparison Computation
    # ----------------------------------------------------
    print("\nComputing comprehensive metric summaries...")
    model_names = ["rule_based", "logistic_regression", "xgboost"]
    pop_metrics_summary: Dict[str, Any] = {}
    comparison_table_rows = []

    for task_name, oof_df, t_col in [("task_a_future_hypo", oof_a_df, "target_hypo_30m"),
                                     ("task_b_impending_onset", oof_b_df, "is_hypo_onset_30m")]:
        y_true = oof_df["true_target"].values
        pop_metrics_summary[task_name] = {}

        for m in model_names:
            prob = oof_df[f"prob_{m}"].values
            # Operational threshold: mean across folds
            thresh = float(np.mean(thresholds_a[m] if task_name == "task_a_future_hypo" else thresholds_b[m]))
            pooled = compute_classification_metrics(y_true, prob, threshold=thresh)
            
            # Participant-level breakdown
            per_p_df = compute_per_participant_metrics(oof_df, target_col="true_target", prob_col=f"prob_{m}", threshold=thresh)
            macro = compute_macro_summary(per_p_df)

            pop_metrics_summary[task_name][m] = {
                "pooled_metrics": pooled,
                "macro_summary": macro,
                "operational_threshold": thresh
            }

            comparison_table_rows.append({
                "task": task_name,
                "model": m,
                "roc_auc_pooled": pooled["roc_auc"],
                "avg_prec_pooled": pooled["average_precision"],
                "f1_pooled": pooled["f1_score"],
                "sensitivity_pooled": pooled["sensitivity"],
                "specificity_pooled": pooled["specificity"],
                "precision_pooled": pooled["precision"],
                "brier_pooled": pooled["brier_score"],
                "roc_auc_macro": macro.get("macro_mean_roc_auc"),
                "avg_prec_macro": macro.get("macro_mean_average_precision")
            })

    # Save population metrics JSON
    pop_metrics_path = eval_dir / "population_metrics.json"
    with open(pop_metrics_path, "w") as f:
        json.dump(pop_metrics_summary, f, indent=2)

    # Save comparison table CSV
    comp_df = pd.DataFrame(comparison_table_rows)
    comp_csv_path = eval_dir / "model_comparison.csv"
    comp_df.to_csv(comp_csv_path, index=False)
    print(f"Saved model comparison table to: {comp_csv_path}")

    # Save participant comparison CSV
    pers_csv_path = eval_dir / "participant_metrics.csv"
    pers_comparison_df.to_csv(pers_csv_path, index=False)
    print(f"Saved participant personalisation table to: {pers_csv_path}")

    # ----------------------------------------------------
    # 5. Error Analysis (Task B Onset with XGBoost)
    # ----------------------------------------------------
    print("Performing subgroup error analysis on Task B (Impending Onset)...")
    error_analysis = perform_error_analysis(oof_b_df, pred_col="pred_xgboost", target_col="true_target")
    err_path = eval_dir / "error_analysis.json"
    with open(err_path, "w") as f:
        json.dump(error_analysis, f, indent=2)
    print(f"Saved error analysis to: {err_path}")

    # ----------------------------------------------------
    # 6. Feature Importance Extraction
    # ----------------------------------------------------
    print("Extracting feature importances...")
    xgb_b = models_b["xgboost"]
    lr_b = models_b["logistic_regression"]

    # XGBoost gain importances
    xgb_imp = dict(zip(config.feature_columns, [float(v) for v in xgb_b.feature_importances_]))
    sorted_xgb_imp = dict(sorted(xgb_imp.items(), key=lambda item: item[1], reverse=True))

    # Logistic Regression coefficients
    lr_coefs = dict(zip(config.feature_columns, [float(v) for v in lr_b.named_steps["classifier"].coef_[0]]))
    sorted_lr_coefs = dict(sorted(lr_coefs.items(), key=lambda item: abs(item[1]), reverse=True))

    feature_importance_data = {
        "xgboost_feature_importance": sorted_xgb_imp,
        "logistic_regression_coefficients": sorted_lr_coefs
    }
    feat_imp_path = eval_dir / "feature_importance.json"
    with open(feat_imp_path, "w") as f:
        json.dump(feature_importance_data, f, indent=2)
    print(f"Saved feature importances to: {feat_imp_path}")

    # ----------------------------------------------------
    # 7. Generate Visualizations
    # ----------------------------------------------------
    print("Generating evaluation figures...")
    generate_evaluation_figures(
        oof_a_df=oof_a_df,
        oof_b_df=oof_b_df,
        pers_b_df=pers_comparison_df,
        output_dir=eval_dir
    )

    # ----------------------------------------------------
    # 8. Model Serialization
    # ----------------------------------------------------
    print("Serializing trained model artifacts...")
    lr_dir = models_dir / "logistic_regression"
    xgb_dir = models_dir / "xgboost"
    lr_dir.mkdir(parents=True, exist_ok=True)
    xgb_dir.mkdir(parents=True, exist_ok=True)

    joblib.dump(models_b["logistic_regression"], lr_dir / "model_task_b_onset.joblib")
    joblib.dump(models_b["xgboost"], xgb_dir / "model_task_b_onset.joblib")
    joblib.dump(models_a["logistic_regression"], lr_dir / "model_task_a_risk.joblib")
    joblib.dump(models_a["xgboost"], xgb_dir / "model_task_a_risk.joblib")

    # ----------------------------------------------------
    # 9. Phase 2 Summary JSON
    # ----------------------------------------------------
    elapsed = round(time.time() - start_time, 2)
    summary = {
        "pipeline_phase": "Phase 2: Baseline ML & Personalisation",
        "execution_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": elapsed,
        "tasks_evaluated": ["task_a_future_hypo", "task_b_impending_onset"],
        "models_evaluated": model_names,
        "n_splits": config.n_splits,
        "total_participants": 25,
        "task_a_sample_count": len(oof_a_df),
        "task_b_sample_count": len(oof_b_df),
        "personalisation_summary": pers_meta,
        "population_headline_results": {
            "task_b_onset_xgboost_roc_auc": pop_metrics_summary["task_b_impending_onset"]["xgboost"]["pooled_metrics"]["roc_auc"],
            "task_b_onset_xgboost_avg_prec": pop_metrics_summary["task_b_impending_onset"]["xgboost"]["pooled_metrics"]["average_precision"],
            "task_b_onset_logreg_roc_auc": pop_metrics_summary["task_b_impending_onset"]["logistic_regression"]["pooled_metrics"]["roc_auc"],
            "task_b_onset_logreg_avg_prec": pop_metrics_summary["task_b_impending_onset"]["logistic_regression"]["pooled_metrics"]["average_precision"],
            "task_b_onset_rule_based_roc_auc": pop_metrics_summary["task_b_impending_onset"]["rule_based"]["pooled_metrics"]["roc_auc"]
        }
    }
    summary_path = eval_dir / "phase2_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved Phase 2 summary to: {summary_path}")

    print("\n" + "=" * 75)
    print(f"PHASE 2 EXPERIMENTS COMPLETED SUCCESSFULLY in {elapsed}s")
    print("=" * 75)
    return summary

if __name__ == "__main__":
    args = parse_args()
    cfg = ExperimentConfig(
        n_splits=args.n_splits,
        random_seed=args.random_seed,
        personalisation_split_ratio=args.personalisation_ratio
    )
    run_phase2_experiments(cfg)
