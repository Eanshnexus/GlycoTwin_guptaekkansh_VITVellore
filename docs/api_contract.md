# GLYCOTWIN — API SPECIFICATION & CONTRACT

**Base URL:** `http://127.0.0.1:8000/api`  
**OpenAPI Specification:** `http://127.0.0.1:8000/openapi.json`  
**Interactive Swagger UI:** `http://127.0.0.1:8000/docs`

---

## 1. System & Diagnostic Endpoints

### 1.1 `GET /`
Returns root application metadata and active documentation URLs.
- **Response (200 OK):**
```json
{
  "project": "GlycoTwin API",
  "version": "1.0.0",
  "description": "Personalised Glucose Digital Twin API",
  "documentation": "/docs",
  "health_check": "/api/health",
  "metadata": "/api/metadata",
  "status": "operational"
}
```

### 1.2 `GET /api/health`
Health and operational readiness probe.
- **Response (200 OK):**
```json
{
  "status": "healthy",
  "app_name": "GlycoTwin API",
  "app_version": "1.0.0",
  "dataset_accessible": true,
  "models_loaded": {
    "rule_based": true,
    "logistic_regression": true,
    "xgboost": true
  },
  "total_participants": 25,
  "total_observations": 309392,
  "timestamp": "2026-10-24T14:00:00Z",
  "details": {
    "dataset_path": "data/processed/glycotwin_features.parquet",
    "environment": "research_prototype",
    "audit_compliance": "PASS WITH CAVEATS"
  }
}
```

### 1.3 `GET /api/metadata`
Frontend-compatible clinical and modeling metadata.
- **Response (200 OK):**
```json
{
  "project_name": "GlycoTwin API",
  "dataset_name": "HUPA-UCM Diabetes Dataset",
  "dataset_provenance": "Hospital Universitario Príncipe de Asturias (HUPA) & Universidad Complutense de Madrid (UCM)",
  "total_participants": 25,
  "total_observations": 309392,
  "prediction_horizon_minutes": 30,
  "hypoglycemia_threshold_mgdl": 70.0,
  "available_tasks": {
    "task_a_future_hypo": "Unconditional prediction of glucose < 70 mg/dL within next 30 minutes",
    "task_b_impending_onset": "Prediction of impending transition < 70 mg/dL within next 30 minutes conditional on current glucose >= 70 mg/dL"
  },
  "available_models": ["rule_based", "logistic_regression", "xgboost"],
  "feature_count": 28,
  "feature_names": ["glucose_current", "glucose_lag_5m", "..."],
  "operational_thresholds": {
    "task_a_future_hypo": {"rule_based": 0.5949, "logistic_regression": 0.8578, "xgboost": 0.8707},
    "task_b_impending_onset": {"rule_based": 0.5506, "logistic_regression": 0.8743, "xgboost": 0.9148}
  },
  "inference_support": {
    "retrospective_cross_validation_evaluation": true,
    "real_time_model_inference": true
  },
  "disclaimer": "Academic research prototype. Not certified for autonomous clinical decisions."
}
```

---

## 2. Participant & Observation Endpoints

### 2.1 `GET /api/patients`
List all anonymized participants with pagination.
- **Query Parameters:**
  - `page` (int, default: 1): Page number.
  - `page_size` (int, default: 25, max: 100): Items per page.
- **Response (200 OK):**
```json
{
  "patients": [
    {
      "participant_id": "HUPA0001P",
      "observation_count": 4096,
      "start_time": "2018-06-13T18:40:00",
      "end_time": "2018-06-27T23:55:00",
      "duration_days": 14.22,
      "available_modalities": ["CGM", "PhysicalActivity", "CSII_Insulin", "Carbohydrates"],
      "has_historical_predictions": true
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 25,
    "total_items": 25,
    "total_pages": 1
  }
}
```

### 2.2 `GET /api/patients/{patient_id}`
Detailed glycemic profile and distribution statistics for one participant.
- **Path Parameters:**
  - `patient_id` (string): Anonymized participant ID (e.g. `HUPA0001P`).
- **Response (200 OK):**
```json
{
  "participant_id": "HUPA0001P",
  "observation_count": 4096,
  "start_time": "2018-06-13T18:40:00",
  "end_time": "2018-06-27T23:55:00",
  "duration_days": 14.22,
  "glucose_stats": {
    "mean": 138.45,
    "std": 48.21,
    "min": 45.0,
    "max": 320.0,
    "tir_percentage": 74.32,
    "tbr_percentage": 4.12,
    "tar_percentage": 21.56
  },
  "available_modalities": ["CGM", "PhysicalActivity", "CSII_Insulin", "Carbohydrates"],
  "has_historical_predictions": true,
  "risk_predictions_count": 4084,
  "onset_predictions_count": 3915
}
```
- **Errors:** `404 Not Found` if participant does not exist.

### 2.3 `GET /api/patients/{patient_id}/observations`
Chronological 5-minute sensor observations for charting.
- **Query Parameters:**
  - `start_time` (string, optional): ISO datetime lower bound.
  - `end_time` (string, optional): ISO datetime upper bound.
  - `limit` (int, default: 100, max: 1000): Items per page.
  - `offset` (int, default: 0): Record offset.
- **Response (200 OK):**
```json
{
  "participant_id": "HUPA0001P",
  "observations": [
    {
      "time": "2018-06-13T19:40:00",
      "glucose": 145.0,
      "calories": 14.5,
      "steps": 120.0,
      "heart_rate": 78.0,
      "basal_rate": 0.08,
      "bolus_volume": 0.0,
      "carb_input": 0.0
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 100,
    "total_items": 4096,
    "total_pages": 41
  }
}
```

### 2.4 `GET /api/patients/{patient_id}/predictions`
Retrieve verified out-of-fold historical cross-validation predictions (Mode A).
- **Query Parameters:**
  - `task` (string, default: "onset"): `"risk"` (Task A) or `"onset"` (Task B).
  - `model` (string, default: "xgboost"): `"rule_based"`, `"logistic_regression"`, `"xgboost"`.
  - `limit` (int, default: 100, max: 1000): Items per page.
  - `offset` (int, default: 0): Offset.
- **Response (200 OK):**
```json
{
  "participant_id": "HUPA0001P",
  "task": "onset",
  "predictions": [
    {
      "participant_id": "HUPA0001P",
      "time": "2018-06-13T19:40:00",
      "task": "task_b_impending_onset",
      "model": "xgboost",
      "predicted_probability": 0.0245,
      "predicted_class": 0,
      "operational_threshold": 0.9148,
      "true_target": 0,
      "cv_fold": 1,
      "horizon_minutes": 30,
      "evaluation_type": "out_of_fold_cross_validation"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 100,
    "total_items": 3915,
    "total_pages": 40
  }
}
```

---

## 3. Model Evaluation & Personalisation Endpoints

### 3.1 `GET /api/models/evaluation`
Returns authoritative Phase 2 cross-validation population performance metrics.
- **Query Parameters:**
  - `task` (string, default: "onset"): `"risk"` (Task A) or `"onset"` (Task B).
- **Response (200 OK):**
```json
{
  "task": "task_b_impending_onset",
  "target_column": "is_hypo_onset_30m",
  "models": [
    {
      "model": "xgboost",
      "task": "task_b_impending_onset",
      "evaluation_method": "5-Fold GroupKFold Cross-Validation across 25 participants",
      "sample_count": 288628,
      "positive_count": 8742,
      "negative_count": 279886,
      "operational_threshold": 0.9148,
      "pooled_metrics": {
        "roc_auc": 0.9702,
        "average_precision": 0.6273,
        "f1_score": 0.5369,
        "sensitivity": 0.4485,
        "specificity": 0.9882,
        "precision": 0.6685,
        "brier_score": 0.0202
      },
      "macro_metrics": {
        "macro_mean_roc_auc": 0.9711,
        "macro_std_roc_auc": 0.0154,
        "macro_mean_average_precision": 0.6325,
        "macro_std_average_precision": 0.0982
      },
      "notes": "Operational threshold (0.9148) selected strictly on training folds via optimal F1."
    }
  ],
  "caveats": [
    "Evaluated on N=25 adult Type 1 diabetes participants.",
    "Pooled metrics combine all out-of-fold records; macro metrics are participant-balanced."
  ]
}
```

### 3.2 `GET /api/models/personalisation`
Returns verified chronological personalisation comparison results with 30-minute purge gap metrics.
- **Query Parameters:**
  - `participant_id` (string, optional): Specific participant filter.
- **Response (200 OK):**
```json
{
  "task": "task_b_impending_onset",
  "adaptation_method": "Platt Scaling (1D Logistic Recalibration on Population Log-Odds)",
  "purge_gap_minutes": 30,
  "total_participants": 25,
  "successful_adaptations": 24,
  "fallback_adaptations": 1,
  "participants": [
    {
      "participant_id": "HUPA0001P",
      "adaptation_status": "personalised",
      "calib_rows_total": 1205,
      "calib_rows_purged": 5,
      "calib_rows_usable": 1200,
      "calib_positives": 38,
      "eval_rows": 2814,
      "eval_positives": 84,
      "t_pop": 0.55,
      "t_pers": 0.042,
      "pop_roc_auc": 0.9621,
      "pers_roc_auc": 0.9621,
      "delta_roc_auc": 0.0,
      "pop_avg_prec": 0.5842,
      "pers_avg_prec": 0.5842,
      "delta_avg_prec": 0.0,
      "pop_f1": 0.5124,
      "pers_f1": 0.5124,
      "delta_f1": 0.0,
      "pop_brier": 0.1491,
      "pers_brier": 0.0216,
      "delta_brier": -0.1275
    }
  ],
  "summary_deltas": {
    "mean_delta_brier": -0.0615,
    "mean_delta_roc_auc": -0.0000,
    "mean_delta_f1": 0.0000,
    "participants_improved_brier": 24
  },
  "caveats": [
    "Evaluated with a 30-minute forward-horizon purge gap preventing target leakage into evaluation period.",
    "Platt scaling improves probability calibration without altering sample ranking."
  ]
}
```

---

## 4. Real-Time Model Inference Endpoint

### 4.1 `POST /api/predictions`
Executes real-time forward model inference (Mode B) using approved deployment model artifacts.
- **Request Body (JSON):**
```json
{
  "task": "onset",
  "model": "xgboost",
  "features": {
    "glucose_current": 115.0,
    "glucose_lag_5m": 118.0,
    "glucose_lag_10m": 122.0,
    "glucose_lag_15m": 128.0,
    "glucose_lag_30m": 135.0,
    "glucose_lag_60m": 142.0,
    "glucose_change_5m": -3.0,
    "glucose_change_15m": -10.0,
    "glucose_change_30m": -20.0,
    "glucose_slope_15m": -0.6667,
    "glucose_slope_30m": -0.6667,
    "glucose_mean_15m": 121.0,
    "glucose_mean_30m": 126.0,
    "glucose_mean_60m": 132.0,
    "glucose_std_30m": 5.2,
    "glucose_std_60m": 8.1,
    "glucose_min_30m": 115.0,
    "glucose_max_30m": 135.0,
    "hour_sin": 0.5,
    "hour_cos": 0.866,
    "weekday_sin": 0.0,
    "weekday_cos": 1.0,
    "recent_calories": 15.0,
    "recent_steps": 100.0,
    "recent_heart_rate": 78.0,
    "recent_basal_rate": 0.08,
    "recent_bolus_volume": 0.0,
    "recent_carb_input": 0.0
  },
  "prediction_time": "2026-10-24T14:00:00Z",
  "participant_id": "OPTIONAL_METADATA"
}
```
- **Response (200 OK):**
```json
{
  "task": "task_b_impending_onset",
  "model": "xgboost",
  "prediction_time": "2026-10-24T14:00:00Z",
  "horizon_minutes": 30,
  "glucose_current": 115.0,
  "predicted_probability": 0.1245,
  "predicted_class": 0,
  "operational_threshold": 0.9148,
  "feature_schema_version": "1.0.0 (28 features)",
  "inference_status": "success",
  "limitation_notice": "Research prototype inference. Not clinically certified for autonomous medical diagnosis."
}
```
- **Validation Error (422 Unprocessable Content):**
  - Current glucose $< 70\text{ mg/dL}$ on Task B:
    `"Task B (Impending Onset) is defined conditionally on current glucose being >= 70.0 mg/dL. Current glucose is 64.0 mg/dL (already in hypoglycemia). Use Task A for unconditional future risk."`
  - Missing required feature:
    `"Missing required feature fields: ['glucose_slope_15m']. Exactly 28 verified features are required."`
  - Target-derived or metadata leakage:
    `"Leakage violation: Forbidden target/metadata field 'target_hypo_30m' cannot be supplied as a model feature."`
