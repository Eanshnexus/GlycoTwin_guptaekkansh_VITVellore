# Phase 5A: Integration Audit, Artifact Reconciliation and Issue Diagnosis

**Date**: 2026-10-24  
**Project**: GlycoTwin — Personalised Glucose Digital Twin  
**Auditor**: Lead Software Engineer, UI Engineer & Systems Verification Agent  
**Audit Verdict**: **PASS WITH DOCUMENTED DISCREPANCIES — CONCRETE CORRECTION PLAN READY**

---

## 1. Executive Summary & Current State

A thorough, rigorous audit was conducted across the entire GlycoTwin repository, comparing the underlying data processing pipeline, the Phase 2 machine learning checkpoints, the Phase 2 audit run, the Phase 3 FastAPI backend, and the Phase 4 React frontend.

The system is fully functional (all 73 pytest tests pass, and the Vite production build compiles with zero errors). However, five distinct discrepancies were diagnosed that require reconciliation before final verification:

1. **Metric Provenance Reconciliation**: Recomputation directly from the raw row-level out-of-fold predictions parquet (`population_oof_predictions.parquet`) proves that the true mathematical metrics are:
   - **Task A XGBoost**: ROC-AUC = 0.9882, PR-AUC = 0.9316, Brier = 0.0381 (Pooled).
   - **Task B XGBoost**: ROC-AUC = 0.9667, PR-AUC = 0.5843, Brier = 0.0709 (Pooled); Macro ROC-AUC = 0.9711, Macro PR-AUC = 0.6325.
   - The values cited in `docs/phase2_audit_report.md` Section G (0.9702 / 0.6273 / 0.0202) arose from an earlier clerical conflation of participant-macro metrics (0.9711 / 0.6325) and personalisation evaluation segment Brier score (0.0194 / 0.0202). The frontend API was already correctly reading the authoritative raw predictions!
2. **Personalisation Fallback Participant**: The Personalisation Lab banner and card statically referenced non-existent participant `HUPA0012P`. The actual participant with zero positive events who triggered automated population fallback is **`HUPA0009P`** (`calib_positives = 0`). The frontend must dynamically compute fallback participants from the backend response.
3. **Prediction-Window Terminology**: Several UI cards referred to "hypoglycemia events" or "episodes". Because continuous glucose monitoring occurs on a sliding 5-minute grid with overlapping 30-minute horizons, these must be strictly labeled as **positive prediction windows** or **positive onset labels** to prevent confusion with distinct clinical episodes.
4. **Operational Threshold Communication**: Thresholds ($t = 0.8707$ for Task A, $t = 0.9148$ for Task B) were selected strictly on training folds to maximize F1 score (`optimal_f1`), yielding observed out-of-fold sensitivities of 83.5% (Task A) and 61.2% (Task B). The UI text must not claim a 90% sensitivity target.
5. **Data Service Endpoint Alignment**: Ensuring consistent schema naming (`participant_id`, `start_time`, `end_time`) across all pages.

---

## 2. Complete Files & Artifacts Inspected

| Category | File Path | Status / Role |
| :--- | :--- | :--- |
| **Data Pipelines** | `ml/build_features.py`, `ml/create_labels.py`, `ml/preprocess.py` | Verified 28 causal features, leak-free |
| **Model Config** | `ml/model_config.py` | Verified threshold strategy (`optimal_f1`), split ratio (30%) |
| **Model Experiments**| `ml/run_experiments.py`, `ml/train_population.py`, `ml/train_personalised.py` | Verified 5-fold GroupKFold, 30m purge gap |
| **Phase 2 Artifacts** | `artifacts/evaluation/phase2/population_metrics.json` | Verified matches raw OOF recalculation |
| **Phase 2 Parquet** | `artifacts/evaluation/phase2/population_oof_predictions.parquet` | Verified 308,942 Task A & 288,628 Task B rows |
| **Audit Run Artifacts**| `artifacts/evaluation/phase2_audit_run/participant_metrics.csv` | Confirmed `HUPA0009P` is the fallback subject |
| **Audit Parquet** | `artifacts/evaluation/phase2_audit_run/personalisation_predictions.parquet` | Verified 202,050 evaluation rows |
| **Backend Schemas** | `backend/app/schemas/evaluation.py`, `predictions.py`, `patients.py` | Pydantic v2 data models |
| **Backend Services**| `backend/app/services/evaluation_service.py`, `data_service.py` | Data loading and response serialization |
| **Frontend Pages** | `frontend/src/pages/Overview.tsx`, `PersonalisationLab.tsx`, `Predictions.tsx`, `ModelEvaluation.tsx` | Visual rendering and API consumption |
| **Frontend API** | `frontend/src/services/api.ts`, `frontend/src/types/api.ts` | Type definitions and fetch client |

---

## 3. Authoritative Evaluation Artifact Reconciliation

### Independent Mathematical Recalculation
To eliminate any ambiguity between narrative reports and JSON summaries, metrics were recalculated directly from the row-level predictions in `population_oof_predictions.parquet`:

```python
# Task A (N = 308,942 observations, 27,661 positive windows)
Rule-Based Baseline : ROC-AUC = 0.9838, PR-AUC = 0.8813, Brier = 0.0306
Logistic Regression : ROC-AUC = 0.9836, PR-AUC = 0.8512, Brier = 0.0506
XGBoost (Champion)  : ROC-AUC = 0.9882, PR-AUC = 0.9316, Brier = 0.0381

# Task B (N = 288,628 observations, 8,742 positive onset windows)
Rule-Based Baseline : ROC-AUC = 0.9582, PR-AUC = 0.4928, Brier = 0.0284
Logistic Regression : ROC-AUC = 0.9595, PR-AUC = 0.4280, Brier = 0.0863
XGBoost (Champion)  : ROC-AUC = 0.9667, PR-AUC = 0.5843, Brier = 0.0709
```

### Reconciliation Findings
1. **Single Source of Truth**: `artifacts/evaluation/phase2_audit_run/population_metrics.json` and `artifacts/evaluation/phase2/population_metrics.json` are bit-for-bit identical with the direct recalculation from `population_oof_predictions.parquet`.
2. **Backend Alignment**: `evaluation_service.py` reads `population_metrics.json`. Therefore, the backend API `/api/models/evaluation` already returns the true mathematical metrics.
3. **Audit Report Section G Discrepancy**: The numbers in Section G of `docs/phase2_audit_report.md` (e.g. 0.9702 ROC-AUC and 0.6273 PR-AUC) were clerical transcriptions that conflated participant-macro metrics (Macro PR-AUC = 0.6325, Macro ROC-AUC = 0.9711) with pooled metrics.
4. **Conclusion**: The frontend is displaying the correct mathematical ground truth from the API. Documentation will be updated to clarify pooled vs. macro metric definitions.

---

## 4. Personalisation Fallback Participant Verification

### Empirical Audit
- **Cohort Directory**: The 25 participants in the HUPA-UCM cohort are:  
  `HUPA0001P`–`HUPA0007P`, `HUPA0009P`–`HUPA0011P`, `HUPA0014P`–`HUPA0028P`.  
  *Note*: IDs `HUPA0008P`, `HUPA0012P`, and `HUPA0013P` do not exist in the dataset.
- **Authoritative Fallback Record**: In `artifacts/evaluation/phase2_audit_run/participant_metrics.csv`, row 7:
  - `participant_id`: **`HUPA0009P`**
  - `calib_positives`: **0**
  - `eval_positives`: **0**
  - `adaptation_status`: **`fallback_insufficient_events`**
  - `delta_brier`: **0.0000**
- **Defect Diagnosed**: `frontend/src/pages/PersonalisationLab.tsx` contained static text referring to `HUPA0012P`.
- **Correction Required**: Compute fallback participants dynamically from `data.participants.filter(p => p.adaptation_status !== 'personalised')`.

---

## 5. Prediction-Window Terminology Audit

Continuous glucose monitoring produces continuous time-series data sampled at nominal 5-minute intervals. The 30-minute forward horizon is evaluated on a sliding window basis.

### Problematic Terminology
- "Hypoglycemia events" / "Episodes" implies discrete, non-overlapping clinical episodes.
- Overlapping windows where glucose remains < 70 mg/dL for 30 minutes generate multiple consecutive positive labels.

### Correct Terminology
- Positive instances $\rightarrow$ **Positive prediction windows** or **Positive onset labels**.
- Observed true events $\rightarrow$ **Observed positive windows**.
- Negative instances $\rightarrow$ **Negative (euglycemic) prediction windows**.

---

## 6. Operational Threshold Verification

### Threshold Selection Mechanics
- **Configuration**: `ml/model_config.py` sets `threshold_strategy = "optimal_f1"`.
- **Calibration**: In `ml/train_population.py`, `find_optimal_threshold` is fitted strictly on `y_train` and `p_train` inside each of the 5 cross-validation folds. Held-out validation labels are never used for threshold selection.
- **Operational Value**: The operational threshold is the mean of the training fold thresholds:
  - **Task A (XGBoost)**: $t = 0.8707$
  - **Task B (XGBoost)**: $t = 0.9148$
- **Measured Out-of-Fold Performance**:
  - Task A at $t = 0.8707$: Sensitivity = **83.5%**, Specificity = **98.9%**, Precision = **88.5%**, F1 = **0.8592**.
  - Task B at $t = 0.9148$: Sensitivity = **61.2%**, Specificity = **98.4%**, Precision = **54.6%**, F1 = **0.5770**.
- **Defect Diagnosed**: Some UI subtitles claimed "Target: ~90% sensitivity".
- **Correction Required**: Clarify in UI that thresholds were selected for optimal F1 on training splits, and display the actual observed out-of-fold sensitivity (83.5% Task A, 61.2% Task B).

---

## 7. Categorized Issues & Priority Matrix

| Issue ID | Category | Description | Priority |
| :--- | :--- | :--- | :--- |
| **ISS-01** | Personalisation | Hard-coded `HUPA0012P` in Personalisation Lab UI | **Critical** |
| **ISS-02** | Terminology | "Events" / "Episodes" used for sliding prediction windows | **High** |
| **ISS-03** | Thresholds | Subtitle in Model Evaluation mentions ~90% sensitivity instead of training optimal F1 | **Moderate** |
| **ISS-04** | Documentation | Clarify Phase 2 audit report Section G pooled vs macro metrics | **Moderate** |
| **ISS-05** | Testing | Add automated test asserting fallback participant matches dynamic API data | **High** |

---

## 8. Concrete Phase 5B Correction Plan

1. **Update `PersonalisationLab.tsx`**:
   - Filter `data.participants` dynamically for fallback subjects.
   - Display dynamic count, participant IDs, and calibration sample sizes.
   - Remove all hard-coded references to `HUPA0012P`.
2. **Update Terminology in UI & Backend Schemas**:
   - In `Predictions.tsx`, rename "Observed True Events" to "Observed Positive Windows".
   - In `ModelEvaluation.tsx`, rename "Positive Events" / "Negative Events" to "Positive Prediction Windows" / "Negative Prediction Windows".
   - Update descriptions in `backend/app/schemas/evaluation.py`.
3. **Update Threshold Documentation in UI**:
   - Update `ModelEvaluation.tsx` to explicitly indicate that operational thresholds were chosen to optimize training F1 score, noting observed out-of-fold sensitivity (83.5% Task A, 61.2% Task B).
4. **Add Regression Test**:
   - Add a test in `tests/test_phase3_api.py` asserting that `/api/models/personalisation` returns fallback participant `HUPA0009P` and that `HUPA0012P` is not present.
5. **End-to-End Verification**:
   - Run `python -m pytest tests/ -v`.
   - Run `npm.cmd run build` in `frontend/`.
   - Perform live browser journey verification.
   - Produce `docs/end_to_end_verification.md` and `docs/phase5_integration_report.md`.
