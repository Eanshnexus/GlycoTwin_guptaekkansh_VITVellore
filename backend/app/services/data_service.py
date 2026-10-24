"""
GlycoTwin Data Service.
Loads, validates, indexes, and caches the verified modelling dataset and historical out-of-fold predictions.
Avoids reading disk on every HTTP request and ensures chronological consistency.
"""
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

from backend.app.config import settings, TASK_ALIASES, OPERATIONAL_THRESHOLDS

class DataService:
    def __init__(self):
        self._df: Optional[pd.DataFrame] = None
        self._oof_df: Optional[pd.DataFrame] = None
        self._patient_ids: List[str] = []
        self._patient_summaries: Dict[str, Dict[str, Any]] = {}
        self._is_loaded = False
        self._load_error: Optional[str] = None

    def initialize(self):
        """Loads and pre-indexes datasets into memory."""
        if self._is_loaded:
            return

        parquet_path = settings.data_parquet_path
        if not parquet_path.exists():
            self._load_error = f"Modelling dataset not found at {parquet_path}"
            raise FileNotFoundError(self._load_error)

        try:
            # 1. Load primary feature dataset
            df = pd.read_parquet(parquet_path)
            # Ensure time is datetime and sorted
            df["time"] = pd.to_datetime(df["time"])
            df = df.sort_values(["participant_id", "time"]).reset_index(drop=True)
            self._df = df

            # 2. Load historical out-of-fold predictions
            oof_path = settings.evaluation_audit_dir / "population_oof_predictions.parquet"
            if not oof_path.exists():
                oof_path = settings.evaluation_phase2_dir / "population_oof_predictions.parquet"

            if oof_path.exists():
                oof_df = pd.read_parquet(oof_path)
                oof_df["time"] = pd.to_datetime(oof_df["time"])
                oof_df = oof_df.sort_values(["participant_id", "time"]).reset_index(drop=True)
                self._oof_df = oof_df
            else:
                self._oof_df = None

            # 3. Precompute participant summaries
            self._patient_ids = sorted(df["participant_id"].unique().tolist())
            self._precompute_patient_summaries()

            self._is_loaded = True
            self._load_error = None
        except Exception as e:
            self._load_error = str(e)
            raise e

    def _precompute_patient_summaries(self):
        """Precomputes summary metrics for each participant for rapid endpoint response."""
        for pid in self._patient_ids:
            p_mask = self._df["participant_id"] == pid
            p_df = self._df[p_mask]

            n_obs = len(p_df)
            t_start = p_df["time"].iloc[0]
            t_end = p_df["time"].iloc[-1]
            duration_days = round((t_end - t_start).total_seconds() / 86400.0, 2)

            g_series = p_df["glucose_current"]
            g_mean = float(g_series.mean())
            g_std = float(g_series.std())
            g_min = float(g_series.min())
            g_max = float(g_series.max())

            tir = float(((g_series >= 70.0) & (g_series <= 180.0)).mean() * 100.0)
            tbr = float((g_series < 70.0).mean() * 100.0)
            tar = float((g_series > 180.0).mean() * 100.0)

            # Available modalities
            modalities = ["CGM"]
            if p_df["recent_heart_rate"].notna().any() and (p_df["recent_heart_rate"] > 0).any():
                modalities.append("HeartRate")
            if p_df["recent_steps"].notna().any() and (p_df["recent_steps"] > 0).any():
                modalities.append("PhysicalActivity")
            if p_df["recent_basal_rate"].notna().any() and (p_df["recent_basal_rate"] > 0).any():
                modalities.append("CSII_Insulin")
            if p_df["recent_carb_input"].notna().any() and (p_df["recent_carb_input"] > 0).any():
                modalities.append("Carbohydrates")

            # Check historical prediction counts
            risk_preds_count = 0
            onset_preds_count = 0
            if self._oof_df is not None:
                p_oof = self._oof_df[self._oof_df["participant_id"] == pid]
                risk_preds_count = int((p_oof["task_name"] == "task_a_future_hypo").sum())
                onset_preds_count = int((p_oof["task_name"] == "task_b_impending_onset").sum())

            self._patient_summaries[pid] = {
                "participant_id": pid,
                "observation_count": n_obs,
                "start_time": t_start.isoformat(),
                "end_time": t_end.isoformat(),
                "duration_days": duration_days,
                "glucose_stats": {
                    "mean": round(g_mean, 2),
                    "std": round(g_std, 2),
                    "min": round(g_min, 2),
                    "max": round(g_max, 2),
                    "tir_percentage": round(tir, 2),
                    "tbr_percentage": round(tbr, 2),
                    "tar_percentage": round(tar, 2)
                },
                "available_modalities": modalities,
                "has_historical_predictions": (risk_preds_count > 0 or onset_preds_count > 0),
                "risk_predictions_count": risk_preds_count,
                "onset_predictions_count": onset_preds_count
            }

    @property
    def is_ready(self) -> bool:
        return self._is_loaded and self._df is not None

    @property
    def total_participants(self) -> int:
        return len(self._patient_ids)

    @property
    def total_observations(self) -> int:
        return len(self._df) if self._df is not None else 0

    def get_patient_ids(self) -> List[str]:
        if not self.is_ready:
            self.initialize()
        return list(self._patient_ids)

    def get_patients_list(self, page: int = 1, page_size: int = 25) -> Tuple[List[Dict[str, Any]], int]:
        if not self.is_ready:
            self.initialize()

        total_items = len(self._patient_ids)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        selected_pids = self._patient_ids[start_idx:end_idx]
        items = []
        for pid in selected_pids:
            s = self._patient_summaries[pid]
            items.append({
                "participant_id": s["participant_id"],
                "observation_count": s["observation_count"],
                "start_time": s["start_time"],
                "end_time": s["end_time"],
                "duration_days": s["duration_days"],
                "available_modalities": s["available_modalities"],
                "has_historical_predictions": s["has_historical_predictions"]
            })
        return items, total_items

    def get_patient_detail(self, patient_id: str) -> Optional[Dict[str, Any]]:
        if not self.is_ready:
            self.initialize()
        return self._patient_summaries.get(patient_id)

    def get_patient_observations(
        self,
        patient_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        if not self.is_ready:
            self.initialize()

        if patient_id not in self._patient_summaries:
            return [], 0

        mask = self._df["participant_id"] == patient_id
        if start_time:
            t_start = pd.to_datetime(start_time)
            mask &= (self._df["time"] >= t_start)
        if end_time:
            t_end = pd.to_datetime(end_time)
            mask &= (self._df["time"] <= t_end)

        filtered = self._df[mask]
        total_matching = len(filtered)
        sliced = filtered.iloc[offset : offset + limit]

        records = []
        for _, row in sliced.iterrows():
            def _safe_float(val):
                return float(val) if pd.notna(val) else None

            records.append({
                "time": row["time"].isoformat(),
                "glucose": float(row["glucose_current"]),
                "calories": _safe_float(row.get("recent_calories")),
                "steps": _safe_float(row.get("recent_steps")),
                "heart_rate": _safe_float(row.get("recent_heart_rate")),
                "basal_rate": _safe_float(row.get("recent_basal_rate")),
                "bolus_volume": _safe_float(row.get("recent_bolus_volume")),
                "carb_input": _safe_float(row.get("recent_carb_input"))
            })

        return records, total_matching

    def get_patient_predictions(
        self,
        patient_id: str,
        task: Optional[str] = None,
        model: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        if not self.is_ready:
            self.initialize()

        if patient_id not in self._patient_summaries:
            return [], 0

        if self._oof_df is None:
            return [], 0

        # Canonicalize task if given
        canonical_task = TASK_ALIASES.get(task.lower(), task) if task else "task_b_impending_onset"
        mask = (self._oof_df["participant_id"] == patient_id) & (self._oof_df["task_name"] == canonical_task)

        filtered = self._oof_df[mask]
        total_matching = len(filtered)
        sliced = filtered.iloc[offset : offset + limit]

        selected_model = model.lower() if model else "xgboost"
        prob_col = f"prob_{selected_model}"
        pred_col = f"pred_{selected_model}"

        # If model is not in oof_df, fallback to xgboost
        if prob_col not in sliced.columns:
            selected_model = "xgboost"
            prob_col = "prob_xgboost"
            pred_col = "pred_xgboost"

        op_thresh = OPERATIONAL_THRESHOLDS.get(canonical_task, {}).get(selected_model, 0.5)

        records = []
        for _, row in sliced.iterrows():
            prob = float(row[prob_col])
            # Use persisted predicted class or apply operational threshold
            pred_class = int(row[pred_col]) if pred_col in row else int(prob >= op_thresh)
            true_target = int(row["true_target"]) if pd.notna(row["true_target"]) else None
            cv_fold = int(row["cv_fold"]) if "cv_fold" in row and pd.notna(row["cv_fold"]) else None

            records.append({
                "participant_id": patient_id,
                "time": row["time"].isoformat(),
                "task": canonical_task,
                "model": selected_model,
                "predicted_probability": round(prob, 4),
                "predicted_class": pred_class,
                "operational_threshold": round(op_thresh, 4),
                "true_target": true_target,
                "cv_fold": cv_fold,
                "horizon_minutes": 30,
                "evaluation_type": "out_of_fold_cross_validation"
            })

        return records, total_matching

data_service = DataService()
