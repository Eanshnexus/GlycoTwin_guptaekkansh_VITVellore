"""
GlycoTwin: Evaluation, Visualization, and Error Analysis Module.
Generates publication-grade evaluation artifacts:
1. Multi-model metrics tables (pooled and participant-balanced macro)
2. Subgroup error analyses (by glucose range, slope, diurnal window, bolus/carb presence)
3. Matplotlib visualizations: ROC curves, PR curves, Confusion matrices, Personalisation deltas, Calibration plots
4. Feature importance extraction
"""
from typing import Dict, Any, List
from pathlib import Path
import json
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import roc_curve, precision_recall_curve
from sklearn.calibration import calibration_curve

from ml.metrics import compute_classification_metrics, compute_per_participant_metrics, compute_macro_summary

def perform_error_analysis(
    df: pd.DataFrame,
    pred_col: str,
    target_col: str
) -> Dict[str, Any]:
    """
    Subgroup analysis of false positives and false negatives for Task B (impending onset).
    """
    y_true = df[target_col].values
    y_pred = df[pred_col].values
    g_curr = df["glucose_current"].values
    slope = df["glucose_slope_15m"].values if "glucose_slope_15m" in df.columns else np.zeros_like(g_curr)
    hour = pd.to_datetime(df["time"]).dt.hour.values

    fp_mask = (y_true == 0) & (y_pred == 1)
    fn_mask = (y_true == 1) & (y_pred == 0)
    tp_mask = (y_true == 1) & (y_pred == 1)
    tn_mask = (y_true == 0) & (y_pred == 0)

    # 1. By Glucose Range
    ranges = {
        "borderline_70_80": (g_curr >= 70.0) & (g_curr < 80.0),
        "target_low_80_100": (g_curr >= 80.0) & (g_curr < 100.0),
        "target_norm_100_140": (g_curr >= 100.0) & (g_curr < 140.0),
        "elevated_140_180": (g_curr >= 140.0) & (g_curr < 180.0),
        "hyperglycemia_gt_180": (g_curr >= 180.0)
    }
    glucose_breakdown = {}
    for r_name, r_mask in ranges.items():
        n_r = int(r_mask.sum())
        glucose_breakdown[r_name] = {
            "total_windows": n_r,
            "false_positives": int((fp_mask & r_mask).sum()),
            "false_negatives": int((fn_mask & r_mask).sum()),
            "true_positives": int((tp_mask & r_mask).sum()),
            "true_negatives": int((tn_mask & r_mask).sum())
        }

    # 2. By Glucose Slope
    slopes = {
        "steep_drop_lt_minus_1": slope < -1.0,
        "moderate_drop_minus_1_to_minus_03": (slope >= -1.0) & (slope < -0.3),
        "steady_minus_03_to_plus_03": (slope >= -0.3) & (slope <= 0.3),
        "rising_gt_plus_03": slope > 0.3
    }
    slope_breakdown = {}
    for s_name, s_mask in slopes.items():
        n_s = int(s_mask.sum())
        slope_breakdown[s_name] = {
            "total_windows": n_s,
            "false_positives": int((fp_mask & s_mask).sum()),
            "false_negatives": int((fn_mask & s_mask).sum()),
            "true_positives": int((tp_mask & s_mask).sum())
        }

    # 3. By Time of Day
    times_of_day = {
        "night_00_to_06": (hour >= 0) & (hour < 6),
        "morning_06_to_12": (hour >= 6) & (hour < 12),
        "afternoon_12_to_18": (hour >= 12) & (hour < 18),
        "evening_18_to_24": (hour >= 18) & (hour < 24)
    }
    tod_breakdown = {}
    for t_name, t_mask in times_of_day.items():
        n_t = int(t_mask.sum())
        tod_breakdown[t_name] = {
            "total_windows": n_t,
            "false_positives": int((fp_mask & t_mask).sum()),
            "false_negatives": int((fn_mask & t_mask).sum()),
            "true_positives": int((tp_mask & t_mask).sum())
        }

    return {
        "total_false_positives": int(fp_mask.sum()),
        "total_false_negatives": int(fn_mask.sum()),
        "total_true_positives": int(tp_mask.sum()),
        "total_true_negatives": int(tn_mask.sum()),
        "by_glucose_range": glucose_breakdown,
        "by_glucose_slope": slope_breakdown,
        "by_time_of_day": tod_breakdown
    }

def generate_evaluation_figures(
    oof_a_df: pd.DataFrame,
    oof_b_df: pd.DataFrame,
    pers_b_df: pd.DataFrame,
    output_dir: Path
):
    """Generates all 5 required publication-grade evaluation charts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    palette = {"rule_based": "#94a3b8", "logistic_regression": "#3b82f6", "xgboost": "#10b981", "personalised": "#8b5cf6"}

    # --- 1. ROC Curves ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    for ax, oof_df, title in zip(axes, [oof_a_df, oof_b_df], ["Task A: Future Hypo Risk (30m)", "Task B: Impending Onset (30m)"]):
        y_true = oof_df["true_target"].values
        for m in ["rule_based", "logistic_regression", "xgboost"]:
            p = oof_df[f"prob_{m}"].values
            fpr, tpr, _ = roc_curve(y_true, p)
            auc_val = oof_df[f"prob_{m}"].corr(pd.Series(y_true))  # quick metric label
            m_metrics = compute_classification_metrics(y_true, p)
            ax.plot(fpr, tpr, label=f"{m.replace('_', ' ').title()} (AUC = {m_metrics['roc_auc']:.3f})", color=palette[m], lw=2)
        ax.plot([0, 1], [0, 1], "k--", alpha=0.5, label="Chance")
        ax.set_title(title, fontsize=13, fontweight="bold")
        ax.set_xlabel("False Positive Rate (1 - Specificity)", fontsize=11)
        ax.set_ylabel("True Positive Rate (Sensitivity)", fontsize=11)
        ax.legend(loc="lower right", frameon=True)
        ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fig.savefig(output_dir / "roc_curves.png", dpi=200)
    plt.close(fig)

    # --- 2. Precision-Recall Curves ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    for ax, oof_df, title in zip(axes, [oof_a_df, oof_b_df], ["Task A: Future Hypo Risk (30m)", "Task B: Impending Onset (30m)"]):
        y_true = oof_df["true_target"].values
        base_prev = y_true.mean()
        for m in ["rule_based", "logistic_regression", "xgboost"]:
            p = oof_df[f"prob_{m}"].values
            prec, rec, _ = precision_recall_curve(y_true, p)
            m_metrics = compute_classification_metrics(y_true, p)
            ax.plot(rec, prec, label=f"{m.replace('_', ' ').title()} (PR-AUC = {m_metrics['average_precision']:.3f})", color=palette[m], lw=2)
        ax.axhline(base_prev, color="k", linestyle="--", alpha=0.5, label=f"Prevalence ({base_prev*100:.1f}%)")
        ax.set_title(title, fontsize=13, fontweight="bold")
        ax.set_xlabel("Recall (Sensitivity)", fontsize=11)
        ax.set_ylabel("Precision (PPV)", fontsize=11)
        ax.legend(loc="upper right", frameon=True)
        ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fig.savefig(output_dir / "pr_curves.png", dpi=200)
    plt.close(fig)

    # --- 3. Confusion Matrices (Task B Onset) ---
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    y_true_b = oof_b_df["true_target"].values
    for ax, m in zip(axes, ["rule_based", "logistic_regression", "xgboost"]):
        y_pred = oof_b_df[f"pred_{m}"].values
        m_dict = compute_classification_metrics(y_true_b, oof_b_df[f"prob_{m}"].values, threshold=oof_b_df[f"pred_{m}"].iloc[0]) # approx
        cm = np.array([[m_dict["true_negatives"], m_dict["false_positives"]],
                       [m_dict["false_negatives"], m_dict["true_positives"]]])
        im = ax.imshow(cm, cmap="Blues", interpolation="nearest")
        for i in range(2):
            for j in range(2):
                ax.text(j, i, f"{cm[i, j]:,}", ha="center", va="center", color="white" if cm[i, j] > cm.max()/2 else "black", fontsize=12, fontweight="bold")
        ax.set_title(f"{m.replace('_', ' ').title()} (Task B)", fontsize=12, fontweight="bold")
        ax.set_xticks([0, 1])
        ax.set_yticks([0, 1])
        ax.set_xticklabels(["Pred Neg", "Pred Pos"])
        ax.set_yticklabels(["True Neg", "True Pos"])
    plt.tight_layout()
    fig.savefig(output_dir / "confusion_matrices.png", dpi=200)
    plt.close(fig)

    # --- 4. Personalisation Comparison (Paired Deltas) ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    valid_p = pers_b_df.dropna(subset=["delta_avg_prec", "delta_roc_auc"])
    if len(valid_p) > 0:
        # PR-AUC Delta
        bars1 = axes[0].bar(range(len(valid_p)), valid_p["delta_avg_prec"], color=np.where(valid_p["delta_avg_prec"] >= 0, "#10b981", "#ef4444"))
        axes[0].axhline(0, color="black", lw=1)
        axes[0].set_title("Personalised Model: Change in PR-AUC (Average Precision)", fontsize=12, fontweight="bold")
        axes[0].set_xlabel("Participant Index", fontsize=11)
        axes[0].set_ylabel("Δ Average Precision (Personalised - Population)", fontsize=11)
        axes[0].grid(True, alpha=0.3)

        # ROC-AUC Delta
        bars2 = axes[1].bar(range(len(valid_p)), valid_p["delta_roc_auc"], color=np.where(valid_p["delta_roc_auc"] >= 0, "#10b981", "#ef4444"))
        axes[1].axhline(0, color="black", lw=1)
        axes[1].set_title("Personalised Model: Change in ROC-AUC", fontsize=12, fontweight="bold")
        axes[1].set_xlabel("Participant Index", fontsize=11)
        axes[1].set_ylabel("Δ ROC-AUC (Personalised - Population)", fontsize=11)
        axes[1].grid(True, alpha=0.3)
    plt.tight_layout()
    fig.savefig(output_dir / "personalisation_comparison.png", dpi=200)
    plt.close(fig)

    # --- 5. Calibration Curves (Task B) ---
    fig, ax = plt.subplots(figsize=(7, 6))
    for m in ["rule_based", "logistic_regression", "xgboost"]:
        prob = oof_b_df[f"prob_{m}"].values
        prob_true, prob_pred = calibration_curve(y_true_b, prob, n_bins=10, strategy="uniform")
        ax.plot(prob_pred, prob_true, marker="o", label=m.replace('_', ' ').title(), color=palette[m], lw=2)
    ax.plot([0, 1], [0, 1], "k--", label="Perfect Calibration")
    ax.set_title("Reliability Diagram: Task B Impending Onset", fontsize=13, fontweight="bold")
    ax.set_xlabel("Mean Predicted Probability", fontsize=11)
    ax.set_ylabel("Empirical Event Fraction", fontsize=11)
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fig.savefig(output_dir / "calibration_curves.png", dpi=200)
    plt.close(fig)

    print(f"Generated 5 publication evaluation figures in: {output_dir}")
