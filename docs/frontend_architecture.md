# GlycoTwin Frontend Architecture & Design Specification

## 1. Executive Summary

GlycoTwin is a personalised glucose digital twin platform developed for predictive diabetes management using the open-access HUPA-UCM Clinical Cohort (25 adult participants with Type 1 Diabetes,Dexcom G6 continuous glucose monitors, and CSII continuous subcutaneous insulin pumps).

The frontend application provides a clinical research digital twin interface built with **React 19**, **TypeScript**, **Vite**, **Tailwind CSS v4**, **Recharts**, and **Lucide React**, fully integrated with the FastAPI Phase 3 backend.

---

## 2. Technical Stack & Dependencies

| Layer | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Framework** | React + TypeScript | 19.2.0 | Reactive component architecture and type safety |
| **Build Tool** | Vite | 8.3.5 | Rapid HMR, dev server, and optimized bundle building |
| **Styling** | Tailwind CSS | 4.3.3 | Modern CSS design system with `@tailwindcss/vite` |
| **Data Visualization** | Recharts | 3.7.0 | SVG charting for time-series and evaluation metrics |
| **Iconography** | Lucide React | 1.16.0 | Clinical and system icons |
| **Routing** | React Router | 7.13.0 | Client-side routing with URL synchronization |
| **API Client** | Native Fetch + Type-safe wrapper | Native | Strongly typed requests and error handling |

---

## 3. Directory Structure

```
frontend/
├── dist/                          # Production bundle outputs
├── src/
│   ├── assets/                    # Static branding icons
│   ├── components/
│   │   ├── charts/
│   │   │   ├── GlucoseTimeSeriesChart.tsx      # CGM trend with hypo (70) and target (70-180) bands
│   │   │   ├── PredictionTimelineChart.tsx     # OOF prediction probabilities with threshold lines
│   │   │   └── PersonalisationDeltaChart.tsx   # Subject-level Brier score paired deltas
│   │   ├── layout/
│   │   │   ├── AppShell.tsx                    # Shared application container
│   │   │   ├── Sidebar.tsx                     # Deep navy sidebar with research footer
│   │   │   └── TopBar.tsx                      # Dynamic breadcrumbs, participant dropdown, health status
│   │   └── shared/
│   │       ├── EmptyState.tsx                  # Informative empty container
│   │       ├── ErrorAlert.tsx                  # Error card with retry handler
│   │       ├── LoadingSkeleton.tsx             # Pulse skeleton loaders
│   │       ├── MetricCard.tsx                  # Clinical metric cards with deltas and badges
│   │       └── StatusBadge.tsx                 # Accessible status pills
│   ├── pages/
│   │   ├── About.tsx                           # Provenance, citations, task definitions, disclaimer
│   │   ├── ModelEvaluation.tsx                 # Cross-validation table, confusion matrix, caveats
│   │   ├── Overview.tsx                        # Executive dashboard, cohort metrics, CGM preview
│   │   ├── Patients.tsx                        # Digital twin telemetry, cohort directory, pagination
│   │   ├── PersonalisationLab.tsx              # Signature research screen: Platt scaling & Brier deltas
│   │   └── Predictions.tsx                     # Mode A historical predictions & Mode B forward inference
│   ├── services/
│   │   └── api.ts                              # Centralized API service connecting to FastAPI
│   ├── types/
│   │   └── api.ts                              # TypeScript schemas matching backend Pydantic models
│   ├── App.css                                 # Minimal root layout overrides
│   ├── App.tsx                                 # Router and global participant state
│   ├── index.css                               # Tailwind v4 import & Inter font typography
│   └── main.tsx                                # React application entrypoint
├── package.json
├── tsconfig.json
└── vite.config.ts                              # Reverse proxy (`/api` -> `http://127.0.0.1:8000`)
```

---

## 4. Visual Identity & Product Design Principles

1. **Information-Dense Clinical Interface**: Designed for a 1440px desktop viewport while remaining fully responsive across mobile and tablet.
2. **Deep Navy & Restrained Teal Palette**:
   - Sidebar: Dark slate navy (`#0a0f1d`)
   - Primary Accent: Restrained clinical teal (`#0d9488` / `#14b8a6`)
   - Supporting Telemetry: Cool blue (`#3b82f6`)
   - Warnings & Thresholds: Amber (`#d97706`)
   - Critical Hypoglycemia Alert: Rose / Red (`#e11d48`)
3. **Rigorous Scientific Integrity**:
   - Every metric originates directly from verified Phase 2 cross-validation or Phase 3 data endpoints.
   - Zero hard-coded performance numbers or fabricated participant profiles in the production path.
   - Visible **"Research Prototype · Retrospective Dataset"** notice across all views.

---

## 5. Screen Specifications

### 5.1 Overview (`/`)
- Cohort summary: 25 participants, 309,392 observations, 100% 5-minute grid.
- Champion Model Highlights: XGBoost GBDT on Task B (96.67% ROC-AUC, 0.627 PR-AUC, 0.0709 Brier score).
- Live CGM preview of the active participant with direct link to the digital twin view.
- Population model comparison table comparing Rule-Based, Logistic Regression, and XGBoost.

### 5.2 Participant Digital Twin (`/patients`, `/patients/:patientId`)
- Cohort Directory sidebar with search and quick-switch capabilities across all 25 participants.
- Patient header displaying monitoring duration (days), observation count, and available sensor streams.
- Interactive Recharts time-series with 70 mg/dL hypo reference line and 70–180 mg/dL target euglycemia band.
- Contextual stream toggles for Heart Rate (bpm), Steps, Basal Insulin, Boluses, and Carbohydrates.
- Window pagination and display-size selector (100 to 1,000 points) to prevent browser DOM overload.

### 5.3 Glucose Predictions & Inference (`/predictions`)
- **Task Selector**:
  - *Task B (Primary)*: Impending Hypoglycaemia Onset conditional on $g_t \ge 70$ mg/dL.
  - *Task A (Secondary)*: Future Hypoglycaemia Risk within 30 minutes.
- **Mode A (Saved Historical Predictions)**:
  - Out-of-fold cross-validation probabilities timeline.
  - Operational threshold cutoff line ($t = 0.9148$ for Task B XGBoost).
  - Chronological inspection table showing model probability, decision, and ground-truth future outcome.
- **Mode B (Forward Research Inference)**:
  - Clinical simulation presets: Rapid Fall, Stable Euglycemia, Borderline Onset, and Hypoglycemic Condition Violation.
  - Real-time feature adjustment for current glucose, slope, bolus volume, and carb intake.
  - Client and server enforcement: Rejects Task B requests if $g_t < 70$ mg/dL with a clear explanatory notice.
  - Displays predicted probability, decision threshold, and research disclaimer.

### 5.4 Personalisation Laboratory (`/personalisation`)
- Signature research screen addressing: *"Does adapting a population-trained model to an individual's history improve future glucose-event prediction?"*
- Aggregate metrics: 24 of 25 participants adapted; mean $\Delta\text{Brier} = -0.0615$ (improved probability calibration); mean $\Delta\text{ROC-AUC} \equiv 0.0000$ (strictly invariant).
- Color-coded paired Brier score delta bar chart across all 25 subjects.
- Subject-by-subject evaluation table with individual sample counts and calibration results.
- Methodological explanation cards explaining Platt log-odds scaling, ranking invariance, and why Participant `HUPA0012P` fell back to the population model.

### 5.5 Model Evaluation & Benchmarking (`/evaluation`)
- Architecture comparison table across 5-fold cross-validation.
- Evaluation sample counts: Positive events vs. Negative events.
- Pooled vs. Participant-Macro metrics comparison.
- Full clinical caveats detailing cohort homogeneity, sensor delay, and non-medical device status.

### 5.6 About & Clinical Data Provenance (`/about`)
- Academic provenance and citation (Hidalgo et al., *Data in Brief* 2024).
- Open-access license reference (CC BY 4.0).
- Formal mathematical formulations of Task A and Task B.
- Comprehensive non-medical device regulatory notice.
