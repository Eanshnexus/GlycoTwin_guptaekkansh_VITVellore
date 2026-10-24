"""
GlycoTwin: Personalisation Experiment Module.
Investigates whether adapting a population-trained model to an individual's
initial historical timeline segment improves prediction of future glucose-risk
events on subsequent unseen observations compared with the population model alone.

Experimental Protocol:
1. For each evaluation participant p:
   a. Split p chronologically: First 30% for Personal Calibration, Last 70% for Evaluation.
   b. Population model: Trained on cohort participants excluding p.
   c. Personalised model: Adapts the population model using p's calibration segment.
      - Fits an adaptation layer (Platt scaling / temperature recalibration + intercept shift).
      - If calibration segment has < 2 positive events, triggers explicit fallback to population model.
   d. Fair Evaluation: Both population and personalised models are evaluated on the
      EXACT SAME future evaluation segment.
"""
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from ml.model_config import ExperimentConfig, DEFAULT_EXPERIMENT_CONFIG
from ml.train_baselines import build_logistic_regression_pipeline
from ml.metrics import compute_classification_metrics, find_optimal_threshold

class PersonalisedAdapter:
    """
    Personalised model adapter that recalibrates population model log-odds
    to individual physiological dynamics using the initial calibration segment.
    """
    def __init__(self, fallback_to_population: bool = False):
        self.fallback_to_population = fallback_to_population
        self.calibrator = None

    def fit(self, pop_logits: np.ndarray, y_calib: np.ndarray):
        if self.fallback_to_population or len(np.unique(y_calib)) < 2:
            self.fallback_to_population = True
            return self

        # Fit 1D logistic regression over population log-odds (Platt scaling)
        # Constrains adaptation to prevent overfitting small calibration windows
        self.calibrator = LogisticRegression(C=0.1, penalty="l2", solver="lbfgs", max_iter=200)
        self.calibrator.fit(pop_logits.reshape(-1, 1), y_calib)
        return self

    def predict_proba(self, pop_probs: np.ndarray) -> np.ndarray:
        if self.fallback_to_population or self.calibrator is None:
            return pop_probs

        # Convert probabilities to log-odds
        p_clipped = np.clip(pop_probs, 1e-6, 1.0 - 1e-6)
        logits = np.log(p_clipped / (1.0 - p_clipped)).reshape(-1, 1)
        pers_probs = self.calibrator.predict_proba(logits)[:, 1]
        return pers_probs

def run_personalisation_experiment(
    df: pd.DataFrame,
    task_name: str,
    target_col: str,
    config: ExperimentConfig = DEFAULT_EXPERIMENT_CONFIG
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Executes the chronological personalisation experiment across all participants.
    
    Returns:
        - eval_predictions_df: Row-level evaluation segment predictions for population and personalised models.
        - participant_comparison_df: Per-participant metric comparisons and deltas.
        - summary_meta: Experiment metadata summary (successful adaptations vs fallbacks).
    """
    feature_cols = config.feature_columns

    # Filter by task eligibility
    if task_name == "task_b_impending_onset":
        mask = df["is_modelling_eligible"] & (df["glucose_current"] >= 70.0) & df[target_col].notna()
    else:
        mask = df["is_modelling_eligible"] & df[target_col].notna()

    task_df = df[mask].copy().sort_values(["participant_id", "time"]).reset_index(drop=True)
    all_pids = sorted(task_df["participant_id"].unique())

    print(f"\n--- Running Personalisation Experiment: {task_name.upper()} ---")
    print(f"Calibration Ratio: {config.personalisation_split_ratio*100:.0f}% initial history | Evaluation: {(1-config.personalisation_split_ratio)*100:.0f}% future holdout")

    eval_preds_list = []
    comparison_records = []
    n_successful_adaptations = 0
    n_fallback_adaptations = 0

    for pid in all_pids:
        # Separate this participant from population
        p_mask = task_df["participant_id"] == pid
        p_df = task_df[p_mask].sort_values("time").reset_index(drop=True)
        other_df = task_df[~p_mask]

        n_p_total = len(p_df)
        n_calib = int(n_p_total * config.personalisation_split_ratio)
        
        # 1. Chronological Split with 30-minute Target Horizon Purge Gap
        raw_calib_df = p_df.iloc[:n_calib]
        eval_df = p_df.iloc[n_calib:].copy()
        n_eval = len(eval_df)
        eval_start_time = eval_df["time"].iloc[0]

        # Purge records in calibration window whose forward 30-minute target horizon crosses into evaluation period
        purge_mask = (raw_calib_df["time"] + pd.Timedelta(minutes=30)) <= eval_start_time
        calib_df = raw_calib_df[purge_mask].copy()
        n_purged = len(raw_calib_df) - len(calib_df)

        # 2. Train Population Model on ALL other participants (Strict Leave-One-Participant-Out)
        X_other = other_df[feature_cols]
        y_other = other_df[target_col].values.astype(int)

        pop_model = build_logistic_regression_pipeline(
            C=config.logreg_params["C"],
            class_weight=config.logreg_params["class_weight"],
            random_state=config.random_seed
        )
        pop_model.fit(X_other, y_other)

        # 3. Predict on calibration segment to fit adapter
        X_calib = calib_df[feature_cols]
        y_calib = calib_df[target_col].values.astype(int)
        calib_positives = int((y_calib == 1).sum())

        # Check adaptation feasibility (must have >= min_calibration_positive_events)
        needs_fallback = calib_positives < config.min_calibration_positive_events
        
        if needs_fallback:
            adapter = PersonalisedAdapter(fallback_to_population=True)
            adapt_status = "fallback_insufficient_events"
            n_fallback_adaptations += 1
        else:
            # Fit adapter on population predictions for calibration segment
            p_calib_pop = pop_model.predict_proba(X_calib)[:, 1]
            p_clipped = np.clip(p_calib_pop, 1e-6, 1.0 - 1e-6)
            logits_calib = np.log(p_clipped / (1.0 - p_clipped))

            adapter = PersonalisedAdapter(fallback_to_population=False)
            adapter.fit(logits_calib, y_calib)
            adapt_status = "personalised"
            n_successful_adaptations += 1

        # 4. Fair Evaluation on the EXACT SAME future evaluation segment
        X_eval = eval_df[feature_cols]
        y_eval = eval_df[target_col].values.astype(int)

        # Unadapted population predictions on evaluation segment
        p_eval_pop = pop_model.predict_proba(X_eval)[:, 1]

        # Personalised predictions on evaluation segment
        p_eval_pers = adapter.predict_proba(p_eval_pop)

        # Calibrate threshold on other participants' training data
        p_other_train = pop_model.predict_proba(X_other)[:, 1]
        t_pop = find_optimal_threshold(y_other, p_other_train, strategy=config.threshold_strategy)

        # Adapted threshold for personalised probabilities to prevent threshold scale mismatch
        if not adapter.fallback_to_population:
            t_pers = float(adapter.predict_proba(np.array([t_pop]))[0])
        else:
            t_pers = t_pop

        # Log row-level evaluation predictions
        eval_df["pop_prob"] = np.round(p_eval_pop, 4)
        eval_df["pers_prob"] = np.round(p_eval_pers, 4)
        eval_df["pop_pred"] = (p_eval_pop >= t_pop).astype(int)
        eval_df["pers_pred"] = (p_eval_pers >= t_pers).astype(int)
        eval_df["adaptation_status"] = adapt_status
        eval_preds_list.append(eval_df[["participant_id", "time", "source_file", target_col, "pop_prob", "pers_prob", "pop_pred", "pers_pred", "adaptation_status"]])

        # Compute participant metrics
        m_pop = compute_classification_metrics(y_eval, p_eval_pop, threshold=t_pop)
        m_pers = compute_classification_metrics(y_eval, p_eval_pers, threshold=t_pers)

        comparison_records.append({
            "participant_id": pid,
            "adaptation_status": adapt_status,
            "calib_rows_total": n_calib,
            "calib_rows_purged": n_purged,
            "calib_rows_usable": len(calib_df),
            "calib_positives": calib_positives,
            "eval_rows": n_eval,
            "eval_positives": m_pop["n_positives"],
            "t_pop": round(t_pop, 4),
            "t_pers": round(t_pers, 4),
            "pop_roc_auc": m_pop["roc_auc"],
            "pers_roc_auc": m_pers["roc_auc"],
            "delta_roc_auc": round(m_pers["roc_auc"] - m_pop["roc_auc"], 4) if (m_pers["roc_auc"] is not None and m_pop["roc_auc"] is not None) else None,
            "pop_avg_prec": m_pop["average_precision"],
            "pers_avg_prec": m_pers["average_precision"],
            "delta_avg_prec": round(m_pers["average_precision"] - m_pop["average_precision"], 4) if (m_pers["average_precision"] is not None and m_pop["average_precision"] is not None) else None,
            "pop_f1": m_pop["f1_score"],
            "pers_f1": m_pers["f1_score"],
            "delta_f1": round(m_pers["f1_score"] - m_pop["f1_score"], 4) if (m_pers["f1_score"] is not None and m_pop["f1_score"] is not None) else None,
            "pop_brier": m_pop["brier_score"],
            "pers_brier": m_pers["brier_score"],
            "delta_brier": round(m_pers["brier_score"] - m_pop["brier_score"], 4) if (m_pers["brier_score"] is not None and m_pop["brier_score"] is not None) else None
        })

    eval_predictions_df = pd.concat(eval_preds_list, ignore_index=True)
    participant_comparison_df = pd.DataFrame(comparison_records)

    summary_meta = {
        "task_name": task_name,
        "total_participants": len(all_pids),
        "successful_adaptations": n_successful_adaptations,
        "fallback_adaptations": n_fallback_adaptations,
        "calibration_ratio": config.personalisation_split_ratio,
        "min_calibration_positive_events": config.min_calibration_positive_events
    }

    print(f"Personalisation Run Complete:")
    print(f"  - Successfully adapted: {n_successful_adaptations}/{len(all_pids)} participants")
    print(f"  - Fallback to population: {n_fallback_adaptations}/{len(all_pids)} participants")

    return eval_predictions_df, participant_comparison_df, summary_meta
