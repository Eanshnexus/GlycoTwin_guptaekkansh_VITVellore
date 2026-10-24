# GLYCOTWIN — MODEL SERVING & INFERENCE PROTOCOL

**Module:** `backend/app/services/model_service.py`  
**Deployment Models:** `artifacts/models/logistic_regression/` and `artifacts/models/xgboost/`  
**Status:** Verified & Operational

---

## 1. Mode A vs Mode B: The Critical Scientific Boundary

A fundamental requirement of the GlycoTwin architecture is preserving the distinction between:
- **Mode A (Retrospective Evaluation Predictions):** Historical predictions generated during 5-Fold GroupKFold cross-validation, where each participant was evaluated strictly by models trained on the other 24 participants. These are persisted in `population_oof_predictions.parquet` and served via `GET /api/patients/{id}/predictions`. They reflect genuine held-out participant performance.
- **Mode B (Real-Time Forward Model Inference):** Inference executed on a client-supplied 28-feature vector using the deployment model artifacts fitted on the complete eligible cohort. These are executed via `POST /api/predictions`.

```
=============================================================================
MODE A: RETROSPECTIVE EVALUATION PREDICTIONS
- Sourced from: artifacts/evaluation/phase2_audit_run/population_oof_predictions.parquet
- Endpoint: GET /api/patients/{id}/predictions
- Property: Strictly held-out out-of-fold predictions; contains true_target and cv_fold.
- Purpose: Timeline auditing, clinical retrospective analysis, model benchmarking.
=============================================================================
MODE B: REAL-TIME DEPLOYMENT INFERENCE
- Sourced from: artifacts/models/{architecture}/model_{task}.joblib
- Endpoint: POST /api/predictions
- Property: Live mathematical scoring of a client-supplied 28-feature vector.
- Purpose: Future event warning simulation, digital twin "what-if" projection.
=============================================================================
```

---

## 2. Model Registry & Operational Thresholds

Operational classification thresholds were calibrated on training folds to maximize clinical F1 score rather than defaulting to arbitrary 0.50:

| Task | Model | Artifact Path | Operational Threshold | F1 Score (Pooled) | PR-AUC (Pooled) | ROC-AUC (Pooled) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **Task A (Risk)** | `rule_based` | In-memory instance | **0.5949** | 0.7770 | 0.8804 | 0.9859 |
| **Task A (Risk)** | `logistic_regression` | `artifacts/models/logistic_regression/model_task_a_risk.joblib` | **0.8578** | 0.7301 | 0.8521 | 0.9818 |
| **Task A (Risk)** | `xgboost` | `artifacts/models/xgboost/model_task_a_risk.joblib` | **0.8707** | **0.8176** | **0.9168** | **0.9882** |
| **Task B (Onset)** | `rule_based` | In-memory instance | **0.5506** | 0.4452 | 0.5471 | 0.9634 |
| **Task B (Onset)** | `logistic_regression` | `artifacts/models/logistic_regression/model_task_b_onset.joblib` | **0.8743** | 0.4230 | 0.4998 | 0.9575 |
| **Task B (Onset)** | `xgboost` | `artifacts/models/xgboost/model_task_b_onset.joblib` | **0.9148** | **0.5369** | **0.6273** | **0.9702** |

---

## 3. Strict Feature Validation & Leakage Guardrails

The inference engine in `model_service.py` executes 6 sequential validation steps on every incoming payload:

1. **Task Canonicalization:** Resolves aliases (`risk` $\to$ `task_a_future_hypo`, `onset` $\to$ `task_b_impending_onset`).
2. **Model Availability Check:** Verifies the model artifact is loaded and initialized.
3. **Leakage & Metadata Exclusion:**
   - Rejects target columns (`target_hypo_30m`, `is_hypo_onset_30m`).
   - Rejects future-derived fields (`future_min_glucose_30m`).
   - Rejects metadata (`participant_id`, `time`, `source_file`, `target_eligible`, `is_modelling_eligible`).
4. **Feature Completeness:** Requires all 28 feature names in `FEATURE_COLUMNS`.
5. **Finite Numeric Assertion:** Asserts that all 28 values are numeric, finite floats (rejects `NaN`, `Inf`, strings).
6. **Task B Clinical Condition:** If `task == "task_b_impending_onset"` and `glucose_current < 70.0 mg/dL`, rejects the request with HTTP 422:
   > *"Task B (Impending Onset) is defined conditionally on current glucose being >= 70.0 mg/dL. Current glucose is X mg/dL (already in hypoglycemia). Use Task A for unconditional future risk."*

---

## 4. Feature Ordering & Inference Execution

Because gradient-boosted trees and serialized pipelines expect strict feature positional ordering, the service constructs a single-row DataFrame using `FEATURE_COLUMNS` as the explicit column index:

```python
X_df = pd.DataFrame([feature_values])[FEATURE_COLUMNS]
prob = float(model_artifact.predict_proba(X_df)[:, 1][0])
pred_class = int(prob >= operational_threshold)
```

This guarantees 100% schema alignment with the trained model checkpoints.
