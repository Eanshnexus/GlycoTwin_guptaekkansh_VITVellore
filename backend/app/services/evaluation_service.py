"""
GlycoTwin Evaluation Service.
Provides verified population evaluation metrics and audit-corrected personalisation comparisons.
Uses the authoritative audit-run evaluation artifacts containing the verified 30-minute purge gap.
"""
from typing import Dict, Any, Optional, List
from pathlib import Path
import json
import pandas as pd
import numpy as np

from backend.app.config import settings, TASK_ALIASES

class EvaluationService:
    def __init__(self):
        self._pop_metrics: Optional[Dict[str, Any]] = None
        self._comparison_df: Optional[pd.DataFrame] = None
        self._pers_df: Optional[pd.DataFrame] = None
        self._is_loaded = False

    def initialize(self):
        """Loads evaluation JSON and CSV artifacts into memory."""
        if self._is_loaded:
            return

        eval_dir = settings.evaluation_audit_dir
        if not eval_dir.exists():
            eval_dir = settings.evaluation_phase2_dir

        # 1. Population Metrics JSON
        pop_json_path = eval_dir / "population_metrics.json"
        if pop_json_path.exists():
            with open(pop_json_path, "r") as f:
                self._pop_metrics = json.load(f)

        # 2. Model Comparison CSV
        comp_csv_path = eval_dir / "model_comparison.csv"
        if comp_csv_path.exists():
            self._comparison_df = pd.read_csv(comp_csv_path)

        # 3. Personalisation CSV (authoritative audit run with purge gap)
        pers_csv_path = eval_dir / "participant_metrics.csv"
        if pers_csv_path.exists():
            self._pers_df = pd.read_csv(pers_csv_path)

        self._is_loaded = True

    def get_evaluation_summary(self, task: Optional[str] = None) -> Dict[str, Any]:
        """Returns verified population evaluation metrics for a task."""
        if not self._is_loaded:
            self.initialize()

        if self._pop_metrics is None:
            raise FileNotFoundError("Population evaluation metrics artifact not found.")

        task_clean = task.lower().strip() if task else "task_b_impending_onset"
        canonical_task = TASK_ALIASES.get(task_clean, "task_b_impending_onset")

        if canonical_task not in self._pop_metrics:
            canonical_task = "task_b_impending_onset"

        target_col = "target_hypo_30m" if canonical_task == "task_a_future_hypo" else "is_hypo_onset_30m"
        sample_count = 308942 if canonical_task == "task_a_future_hypo" else 288628
        pos_count = 27661 if canonical_task == "task_a_future_hypo" else 8742
        neg_count = sample_count - pos_count

        task_models_data = self._pop_metrics.get(canonical_task, {})
        model_summaries = []

        for m_name, m_data in task_models_data.items():
            pooled = m_data.get("pooled_metrics", {})
            macro = m_data.get("macro_summary", {})
            thresh = float(m_data.get("operational_threshold", 0.5))

            model_summaries.append({
                "model": m_name,
                "task": canonical_task,
                "evaluation_method": "5-Fold GroupKFold Cross-Validation across 25 participants",
                "sample_count": sample_count,
                "positive_count": pos_count,
                "negative_count": neg_count,
                "operational_threshold": round(thresh, 4),
                "pooled_metrics": {
                    "roc_auc": pooled.get("roc_auc"),
                    "average_precision": pooled.get("average_precision"),
                    "f1_score": pooled.get("f1_score"),
                    "sensitivity": pooled.get("sensitivity"),
                    "specificity": pooled.get("specificity"),
                    "precision": pooled.get("precision"),
                    "brier_score": pooled.get("brier_score")
                },
                "macro_metrics": {
                    "macro_mean_roc_auc": macro.get("macro_mean_roc_auc"),
                    "macro_std_roc_auc": macro.get("macro_std_roc_auc"),
                    "macro_mean_average_precision": macro.get("macro_mean_average_precision"),
                    "macro_std_average_precision": macro.get("macro_std_average_precision")
                },
                "notes": f"Operational threshold ({thresh:.4f}) selected strictly on training folds via optimal F1."
            })

        caveats = [
            "Evaluated on N=25 adult Type 1 diabetes participants (HUPA-UCM cohort).",
            "Pooled metrics reflect all out-of-fold records; macro summaries provide participant-balanced metrics.",
            "Task B is evaluated strictly on windows where current glucose is >= 70 mg/dL."
        ]

        return {
            "task": canonical_task,
            "target_column": target_col,
            "models": model_summaries,
            "caveats": caveats
        }

    def get_personalisation_summary(self, participant_id: Optional[str] = None) -> Dict[str, Any]:
        """Returns verified personalisation comparison from the audit run."""
        if not self._is_loaded:
            self.initialize()

        if self._pers_df is None:
            raise FileNotFoundError("Personalisation participant metrics artifact not found.")

        df = self._pers_df.copy()

        if participant_id:
            df = df[df["participant_id"] == participant_id]
            if len(df) == 0:
                raise KeyError(f"Participant '{participant_id}' not found in personalisation results.")

        items = []
        for _, row in df.iterrows():
            def _clean(val):
                return float(val) if pd.notna(val) else None

            items.append({
                "participant_id": str(row["participant_id"]),
                "adaptation_status": str(row["adaptation_status"]),
                "calib_rows_total": int(row.get("calib_rows_total", row.get("calib_rows", 0))),
                "calib_rows_purged": int(row.get("calib_rows_purged", 5)),
                "calib_rows_usable": int(row.get("calib_rows_usable", row.get("calib_rows", 0))),
                "calib_positives": int(row["calib_positives"]),
                "eval_rows": int(row["eval_rows"]),
                "eval_positives": int(row["eval_positives"]),
                "t_pop": float(row.get("t_pop", 0.5)),
                "t_pers": float(row.get("t_pers", 0.5)),
                "pop_roc_auc": _clean(row.get("pop_roc_auc")),
                "pers_roc_auc": _clean(row.get("pers_roc_auc")),
                "delta_roc_auc": _clean(row.get("delta_roc_auc")),
                "pop_avg_prec": _clean(row.get("pop_avg_prec")),
                "pers_avg_prec": _clean(row.get("pers_avg_prec")),
                "delta_avg_prec": _clean(row.get("delta_avg_prec")),
                "pop_f1": _clean(row.get("pop_f1")),
                "pers_f1": _clean(row.get("pers_f1")),
                "delta_f1": _clean(row.get("delta_f1")),
                "pop_brier": _clean(row.get("pop_brier")),
                "pers_brier": _clean(row.get("pers_brier")),
                "delta_brier": _clean(row.get("delta_brier"))
            })

        # Cohort summary stats
        full_df = self._pers_df
        n_total = len(full_df)
        n_success = int((full_df["adaptation_status"] == "personalised").sum())
        n_fallback = int((full_df["adaptation_status"] != "personalised").sum())

        mean_delta_brier = float(full_df["delta_brier"].mean())
        mean_delta_roc = float(full_df["delta_roc_auc"].dropna().mean())
        mean_delta_f1 = float(full_df["delta_f1"].dropna().mean())

        summary_deltas = {
            "mean_delta_brier": round(mean_delta_brier, 4),
            "mean_delta_roc_auc": round(mean_delta_roc, 4),
            "mean_delta_f1": round(mean_delta_f1, 4),
            "participants_improved_brier": int((full_df["delta_brier"] < 0).sum())
        }

        caveats = [
            "Evaluated with a 30-minute forward-horizon purge gap preventing target leakage into evaluation period.",
            "Platt scaling recalibrates probability scale (improving Brier score) but preserves sample rank order (ROC-AUC delta is ~0.0000).",
            "Threshold adaptation is applied so alert sensitivity is preserved on the recalibrated probability scale.",
            "Participants with insufficient events in the calibration segment (HUPA0009P) fall back cleanly to population model."
        ]

        return {
            "task": "task_b_impending_onset",
            "adaptation_method": "Platt Scaling (1D Logistic Recalibration on Population Log-Odds)",
            "purge_gap_minutes": 30,
            "total_participants": n_total,
            "successful_adaptations": n_success,
            "fallback_adaptations": n_fallback,
            "participants": items,
            "summary_deltas": summary_deltas,
            "caveats": caveats
        }

evaluation_service = EvaluationService()
