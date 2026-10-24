"""
GlycoTwin: Evaluation Metrics Module.
Calculates clinical and statistical classification metrics:
ROC-AUC, Average Precision (PR-AUC), Sensitivity (Recall),
Specificity, Precision, F1-score, Brier score, and Confusion Matrix.
Handles edge cases (e.g. 0 positive events in participant timeline) transparently.
"""
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    precision_score,
    recall_score,
    f1_score,
    brier_score_loss,
    confusion_matrix,
    roc_curve,
    precision_recall_curve
)

def find_optimal_threshold(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    strategy: str = "optimal_f1",
    target_sensitivity: float = 0.80
) -> float:
    """
    Determines classification threshold using training data only.
    Strategies:
        - "optimal_f1": Threshold that maximizes F1 score.
        - "target_sensitivity": Threshold achieving target sensitivity (e.g. 80%).
        - "fixed_0.5": Default 0.5 threshold.
    """
    if strategy == "fixed_0.5":
        return 0.5

    if len(np.unique(y_true)) < 2:
        return 0.5

    prec, rec, thresholds = precision_recall_curve(y_true, y_prob)
    
    if strategy == "optimal_f1":
        # Calculate F1 for each threshold
        f1_scores = np.zeros_like(thresholds)
        for i in range(len(thresholds)):
            p = prec[i]
            r = rec[i]
            f1_scores[i] = (2 * p * r) / (p + r) if (p + r) > 0 else 0.0
        best_idx = np.argmax(f1_scores) if len(f1_scores) > 0 else 0
        best_thresh = float(thresholds[best_idx]) if len(thresholds) > 0 else 0.5
        # Guard against degenerate boundaries
        return float(np.clip(best_thresh, 0.05, 0.95))

    elif strategy == "target_sensitivity":
        # Find threshold where recall is closest to target_sensitivity
        valid_idx = np.where(rec[:-1] >= target_sensitivity)[0]
        if len(valid_idx) > 0:
            best_idx = valid_idx[-1]
            return float(thresholds[best_idx])
        return 0.5

    return 0.5

def compute_classification_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    threshold: float = 0.5
) -> Dict[str, Any]:
    """
    Computes full set of binary classification metrics.
    Gracefully handles cohorts or participants with single-class outcomes.
    """
    y_true = np.asarray(y_true, dtype=int)
    y_prob = np.asarray(y_prob, dtype=float)
    y_pred = (y_prob >= threshold).astype(int)

    n_samples = len(y_true)
    n_pos = int((y_true == 1).sum())
    n_neg = int((y_true == 0).sum())

    # Default values for edge cases
    metrics: Dict[str, Any] = {
        "n_samples": n_samples,
        "n_positives": n_pos,
        "n_negatives": n_neg,
        "prevalence_pct": round(n_pos / n_samples * 100.0, 2) if n_samples > 0 else 0.0,
        "threshold": round(float(threshold), 4),
        "roc_auc": None,
        "average_precision": None,
        "brier_score": None,
        "sensitivity": None,
        "specificity": None,
        "precision": None,
        "f1_score": None,
        "true_positives": 0,
        "false_positives": 0,
        "true_negatives": 0,
        "false_negatives": 0,
        "is_degenerate": False
    }

    if n_samples == 0:
        metrics["is_degenerate"] = True
        return metrics

    # Probabilistic Brier score
    metrics["brier_score"] = round(float(brier_score_loss(y_true, y_prob)), 4)

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    metrics["true_positives"] = int(tp)
    metrics["false_positives"] = int(fp)
    metrics["true_negatives"] = int(tn)
    metrics["false_negatives"] = int(fn)

    # Specificity
    metrics["specificity"] = round(float(tn / (tn + fp)), 4) if (tn + fp) > 0 else None

    # Degenerate: only 1 class present
    if n_pos == 0 or n_neg == 0:
        metrics["is_degenerate"] = True
        # If no positives, recall and PR-AUC/ROC-AUC are mathematically undefined
        return metrics

    # Discrimination metrics
    try:
        metrics["roc_auc"] = round(float(roc_auc_score(y_true, y_prob)), 4)
    except Exception:
        metrics["roc_auc"] = None

    try:
        metrics["average_precision"] = round(float(average_precision_score(y_true, y_prob)), 4)
    except Exception:
        metrics["average_precision"] = None

    # Threshold-dependent metrics
    metrics["sensitivity"] = round(float(tp / (tp + fn)), 4) if (tp + fn) > 0 else 0.0
    metrics["precision"] = round(float(tp / (tp + fp)), 4) if (tp + fp) > 0 else 0.0
    metrics["f1_score"] = round(float(f1_score(y_true, y_pred, zero_division=0)), 4)

    return metrics

def compute_per_participant_metrics(
    df: pd.DataFrame,
    target_col: str,
    prob_col: str,
    threshold: float = 0.5
) -> pd.DataFrame:
    """
    Computes classification metrics broken down by individual participant.
    """
    rows = []
    for pid, group in df.groupby("participant_id"):
        y_true = group[target_col].values
        y_prob = group[prob_col].values
        m = compute_classification_metrics(y_true, y_prob, threshold=threshold)
        m["participant_id"] = pid
        rows.append(m)

    res_df = pd.DataFrame(rows)
    # Reorder columns with participant_id first
    cols = ["participant_id", "n_samples", "n_positives", "n_negatives", "prevalence_pct",
            "roc_auc", "average_precision", "sensitivity", "specificity", "precision", "f1_score", "brier_score"]
    available_cols = [c for c in cols if c in res_df.columns]
    return res_df[available_cols]

def compute_macro_summary(participant_metrics_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes participant-balanced macro-average summary statistics across all participants
    where metrics are well-defined.
    """
    metric_cols = ["roc_auc", "average_precision", "sensitivity", "specificity", "precision", "f1_score", "brier_score"]
    summary: Dict[str, Any] = {}
    for col in metric_cols:
        if col in participant_metrics_df.columns:
            valid_vals = participant_metrics_df[col].dropna()
            if len(valid_vals) > 0:
                summary[f"macro_mean_{col}"] = round(float(valid_vals.mean()), 4)
                summary[f"macro_std_{col}"] = round(float(valid_vals.std()), 4)
                summary[f"macro_median_{col}"] = round(float(valid_vals.median()), 4)
                summary[f"n_participants_eval_{col}"] = len(valid_vals)
            else:
                summary[f"macro_mean_{col}"] = None
    return summary
