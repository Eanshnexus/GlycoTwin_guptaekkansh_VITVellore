# Phase 4 Completion Report: React Frontend, Digital Twin Dashboard & Predictions Laboratory

**Date**: 2026-10-24  
**Project**: GlycoTwin — Personalised Glucose Digital Twin  
**Lead Engineer**: Lead Software Engineer, UI Engineer & ML Systems Architect  
**Final Status**: **PASS — Phase 4 Frontend Complete & Verified**

---

## 1. Executive Summary

Phase 4 of the GlycoTwin project has been successfully completed. A responsive, highly polished, clinical-research React frontend was developed from scratch in `frontend/` using **React 19**, **TypeScript**, **Vite**, **Tailwind CSS v4**, **Recharts**, and **Lucide React**, fully integrated with the Phase 3 FastAPI backend.

The implementation strictly adheres to the core scientific principles established in Phases 0 through 3:
- **Zero Mock Metrics**: All numbers, tables, and charts reflect genuine Phase 1 processed data, verified Phase 2 cross-validation artifacts, and Phase 3 model endpoints.
- **Strict Mode A vs. Mode B Separation**: Mode A presents historical out-of-fold cross-validated prediction records with known retrospective labels; Mode B provides real-time forward model inference with clinical simulation presets.
- **Strict Task A vs. Task B Separation**: Distinguishes between unconditional 30-minute risk (Task A) and impending hypoglycemia onset conditional on $g_t \ge 70$ mg/dL (Task B).
- **Personalisation Experiment**: Fully showcases the signature Platt log-odds scaling adaptation across all 25 participants, illustrating why Brier score improves ($\Delta = -0.0615$) while ranking discrimination remains invariant ($\Delta = 0.0000$), and explaining Participant `HUPA0012P`'s automated population fallback.

---

## 2. Screens Implemented & Verified

| Route | Page Component | Key Functionality & Verification |
| :--- | :--- | :--- |
| `/` | `Overview.tsx` | Cohort metadata (25 participants, 309,392 points), XGBoost champion metrics (96.67% AUC, 0.627 PR-AUC), active participant CGM preview, and multi-model benchmark table. |
| `/patients` | `Patients.tsx` | Participant directory with search and switch controls, glycemic range statistics (TIR, TBR, TAR), interactive CGM Recharts time-series with 70 mg/dL hypo reference and target bands, contextual biometrics toggles (heart rate, steps), and window pagination. |
| `/predictions` | `Predictions.tsx` | Task switcher (Task A vs Task B), Mode A historical OOF predictions timeline with decision cutoffs and ground-truth markers, and Mode B interactive forward inference form with clinical presets and $g_t \ge 70$ validation. |
| `/personalisation` | `PersonalisationLab.tsx` | Core hypothesis banner, 25-participant Brier delta bar chart, Platt scaling ranking invariance explanation, and complete subject-by-subject evaluation table. |
| `/evaluation` | `ModelEvaluation.tsx` | Comprehensive 5-fold cross-validation architecture table (Rule-Based, Logistic Regression, XGBoost), sample counts, pooled vs. participant-macro breakdowns, and clinical caveats. |
| `/about` | `About.tsx` | HUPA-UCM dataset provenance and citation (Hidalgo et al. 2024), CC BY 4.0 license, task formulations, software stack, and non-medical device regulatory notice. |

---

## 3. Backend Integration & Verification

All 7 API services were integrated into `frontend/src/services/api.ts` and verified end-to-end against the running FastAPI backend:

1. `GET /api/health` -> Verified: `200 OK`, all models loaded, dataset accessible.
2. `GET /api/metadata` -> Verified: `200 OK`, 25 participants, 309,392 observations.
3. `GET /api/patients` -> Verified: `200 OK`, returns paginated cohort list.
4. `GET /api/patients/{id}` -> Verified: `200 OK`, loaded `HUPA0001P` details.
5. `GET /api/patients/{id}/observations` -> Verified: `200 OK`, 120 and 300-point windows loaded and plotted.
6. `GET /api/patients/{id}/predictions` -> Verified: `200 OK`, historical OOF predictions plotted on timeline.
7. `GET /api/models/evaluation?task=onset` -> Verified: `200 OK`, multi-model benchmark table rendered.
8. `GET /api/models/personalisation` -> Verified: `200 OK`, 24 adapted, 1 fallback, Brier deltas plotted.
9. `POST /api/predictions` -> Verified: `200 OK`, executed forward inference yielding probability and alert decision.

---

## 4. Verification & Testing Results

1. **Frontend Production Build**:
   - Command: `npm.cmd run build` (runs `tsc -b && vite build`)
   - Result: **0 errors, 0 warnings**, built in 15.71s (`dist/` generated successfully).
2. **Backend Regression Test Suite**:
   - Command: `python -m pytest tests/ -v`
   - Result: **73 of 73 tests passed** in 25.97s.
3. **End-to-End Browser Automation**:
   - Automated browser subagent navigated through all 6 pages, executed Mode B forward inference, switched tasks, and captured full-page screenshots.
   - Screenshots generated:
     - `overview_page_1792833851776.png`
     - `patients_page_1792833874665.png`
     - `predictions_page_1792833888663.png`
     - `predictions_mode_b_active_1792833944042.png`
     - `inference_output_1792833989142.png`
     - `personalisation_page_1792834018024.png`
     - `evaluation_page_1792834047464.png`
     - `about_page_1792834075406.png`

---

## 5. Startup Commands

### Start the Backend (Port 8000)
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

### Start the Frontend Dev Server (Port 5173)
```bash
cd frontend
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

Open `http://127.0.0.1:5173/` in your browser.

---

## 6. Final Verdict

**PASS** — Phase 4 is complete, verified, and ready for demonstration. The application connects verified data processing, evaluated machine-learning models, a functioning Python API, and an interactive React frontend into a unified digital twin platform.
