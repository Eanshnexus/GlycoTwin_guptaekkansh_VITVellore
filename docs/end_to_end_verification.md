# GlycoTwin — End-to-End Application Verification

**Environment:** Windows 11 / Python 3.13 / Node.js v22.14.0 / Vite 8.3.5 / FastAPI  
**Dataset:** HUPA-UCM Type 1 Diabetes Dataset (25 participants, 5-minute sampling interval)  
**Verification Date:** October 2026  
**Status:** FULLY VERIFIED (PASS)

---

## 1. Verification Scope & Methodology

This document records the empirical end-to-end verification of the GlycoTwin digital twin application across all layers: backend FastAPI services, data pipelines, serialized machine learning models, cross-validation evaluation artifacts, and the React/TypeScript frontend.

Verification was conducted via:
1. **Automated Unit & Integration Test Suites:** 75 pytest tests covering data pipelines, leakage resistance, model serving, inference validation, and Phase 5 regression tests.
2. **Frontend Type Checking & Bundle Verification:** `tsc -b` and `vite build` completed with zero errors.
3. **Live Headless Browser Automation:** End-to-end user journeys executed against running backend (`http://127.0.0.1:8000`) and frontend (`http://127.0.0.1:5173`).

---

## 2. 17-Point User Journey Verification Results

| # | Checkpoint | Target Behavior | Observed Behavior | Status |
|---|---|---|---|---|
| **1** | **Application Launch** | Frontend and Backend dev servers start cleanly without port collisions. | Backend bound to `127.0.0.1:8000`, Frontend bound to `127.0.0.1:5173`. | **PASS** |
| **2** | **Backend Connection** | Live status indicator in UI header shows green connected badge. | `GET /api/health` returns `status: "healthy"`; UI displays green "Backend Connected" pill. | **PASS** |
| **3** | **Overview Metadata** | Platform metrics load dynamically from dataset and pipeline summaries. | Cohort: 25 participants, 308,942 records, 28 engineered features, zero synthetic records. | **PASS** |
| **4** | **Evaluation Metrics** | Macro and pooled out-of-fold metrics display authoritative Phase 2 results. | Task A: ROC-AUC 0.9882, PR-AUC 0.9316; Task B: ROC-AUC 0.9667, PR-AUC 0.5843. | **PASS** |
| **5** | **Participant Selection** | Dropdown populates all 25 valid HUPA IDs (`HUPA0001P`–`HUPA0028P`). | All 25 participants selectable; `HUPA0012P` is verified absent from the cohort. | **PASS** |
| **6** | **Participant Summary** | Demographics, TIR, TAR, TBR, and HbA1c metrics update dynamically. | Correctly displays mean glucose, CV, time in ranges, and sensor session bounds. | **PASS** |
| **7** | **Historical Observations** | Chronological CGM traces display with hypoglycaemia safety zones (<70 mg/dL). | Time-series chart renders observations with interactive hover tooltips and range markers. | **PASS** |
| **8** | **Date-Range Filtering** | Date pickers query bounded intervals via `/api/patients/{id}/observations`. | Correctly queries `start_time` and `end_time` without unbounded memory overhead. | **PASS** |
| **9** | **Real API Data Delivery** | Zero synthetic or fabricated CGM observations rendered in UI. | All points match Parquet partition records in `data/processed/modelling_dataset.parquet`. | **PASS** |
| **10** | **Historical Predictions** | Mode A renders verified 5-fold cross-validation held-out predictions. | Displays predicted probability timeline alongside true future onset ground truth. | **PASS** |
| **11** | **Task A vs Task B** | Preconditions and target horizons strictly separated. | Task A (All-Risk) vs Task B (Impending Onset with glucose >=70 mg/dL) never conflated. | **PASS** |
| **12** | **Prediction Provenance** | Historical timeline displays explicit out-of-fold cross-validation tags. | Explicitly distinguishes Mode A (retrospective CV) from Mode B (real-time inference). | **PASS** |
| **13** | **Personalisation Lab** | Shows 30% calibration / 70% evaluation split with 30m purge gap. | 24 participants successfully adapted with personalized threshold shifts. | **PASS** |
| **14** | **Fallback Messaging** | Data-driven notice displayed for participants with insufficient calibration events. | Correctly identifies `HUPA0009P` (0 calibration positive windows); no static strings. | **PASS** |
| **15** | **Metric Consistency** | Overview, Evaluation, and Personalisation cards display consistent numbers. | All pages read from `/api/models/evaluation` and `/api/models/personalisation`. | **PASS** |
| **16** | **Clinical Explanations** | About page explains clinical dataset, GroupKFold CV, and safety disclaimers. | Clear disclaimers stating predictions do not constitute automated insulin delivery. | **PASS** |
| **17** | **Error & Edge Handling** | Invalid queries, missing participants, and leakage fields rejected with 4xx codes. | Verified 404 for unknown IDs, 422 for Task B precondition violations (<70 mg/dL). | **PASS** |

---

## 3. Real-Time Inference Validation (Mode B)

Inference testing was conducted via `POST /api/predictions`:
1. **Task A (Hypoglycaemia Risk):**
   - Valid 28-feature input evaluated with XGBoost pipeline.
   - Returned `predicted_probability = 0.0818`, `risk_level = "low"`, threshold `0.8707`.
2. **Task B (Impending Onset):**
   - Valid input with current glucose `120.0 mg/dL` returned probability `0.0094`, threshold `0.9148`.
3. **Target Precondition Enforcement:**
   - Input with `glucose_current = 62.0 mg/dL` submitted to Task B correctly rejected with `HTTP 422 Unprocessable Content` ("Task B is defined conditionally on current glucose being >= 70.0 mg/dL").
4. **Target Leakage Rejection:**
   - Input containing forbidden field `future_min_glucose_30m` rejected with `HTTP 422` ("Leakage violation: 'future_min_glucose_30m' is a target-derived future field").
5. **Missing Feature Rejection:**
   - Input missing `glucose_lag_5m` rejected with `HTTP 422` ("Missing required feature fields").

---

## 4. Test Execution Record

```text
============================= test session starts =============================
platform win32 -- Python 3.13.2, pytest-8.3.5
rootdir: C:\Users\gupta\Desktop\GlycoTwin
collected 75 items

tests/test_phase0_audit.py::test_local_dataset_audit_when_available PASSED [  1%]
tests/test_phase1_pipeline.py::test_load_valid_participant PASSED        [  2%]
...
tests/test_phase3_api.py::test_personalisation_fallback_participant_identity PASSED [ 76%]
tests/test_phase3_api.py::test_evaluation_threshold_and_metrics_consistency PASSED [ 77%]
tests/test_phase3_data_service.py::test_data_service_initialization PASSED [ 78%]
tests/test_phase3_predictions.py::test_non_finite_feature_rejection PASSED [100%]

====================== 75 passed, 64 warnings in 17.15s =======================
```

Frontend Production Build:
```text
> frontend@0.0.0 build
> tsc -b && vite build

vite v8.3.5 building client environment for production...
transforming...
✓ 2532 modules transformed.
rendering chunks...
dist/index.html                   0.45 kB │ gzip:   0.29 kB
dist/assets/index-oesnWOqu.css   41.39 kB │ gzip:   7.70 kB
dist/assets/index-CREKeypE.js   766.81 kB │ gzip: 219.29 kB
✓ built in 1.53s
```

---

## 5. Visual Artifacts Captured

During browser subagent verification, high-resolution visual evidence was captured:
1. `overview_page_1792833851776.png`: Platform dashboard showing 25 participants, 308k rows, 28 features.
2. `patients_page_1792833874665.png`: Patient twin view for `HUPA0001P` with interactive CGM time-series.
3. `predictions_page_1792833888663.png`: Mode A retrospective held-out predictions timeline.
4. `predictions_mode_b_active_1792833944042.png`: Mode B real-time inference interactive tester with risk assessment.
5. `personalisation_page_1792834018024.png`: Personalisation Lab showing verified dynamic banner for `HUPA0009P` (0 calibration positive windows).
6. `model_evaluation_task_a_1792836065624.png`: Model Evaluation page with updated prediction window labels and threshold documentation.
7. `about_page_1792834075406.png`: Clinical provenance and regulatory disclaimers.
