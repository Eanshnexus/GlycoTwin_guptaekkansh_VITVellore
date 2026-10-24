# GlycoTwin Frontend API Integration & Data Flow Guide

## 1. Overview

The GlycoTwin frontend interacts with the FastAPI Phase 3 backend via a centralized, strongly typed API client (`src/services/api.ts`). In development mode, Vite's internal reverse proxy forwards `/api` requests to `http://127.0.0.1:8000`, eliminating CORS issues and keeping API endpoints relative.

---

## 2. API Endpoint Mapping

| Frontend View / Component | Backend HTTP Endpoint | Schema / Method | Description |
| :--- | :--- | :--- | :--- |
| **TopBar** | `GET /api/health` | `HealthResponse` | Real-time backend connectivity and model load health check |
| **Overview** | `GET /api/metadata` | `MetadataResponse` | Cohort metadata, observation counts, and available models |
| **Overview** | `GET /api/models/evaluation?task=onset` | `EvaluationResponse` | Population benchmark metrics for Task B |
| **Patients** | `GET /api/patients?page=1&page_size=25` | `PatientListResponse` | Cohort directory listing all 25 participants |
| **Patients** | `GET /api/patients/{id}` | `PatientDetail` | Selected participant summary, duration, and modalities |
| **Patients / Overview** | `GET /api/patients/{id}/observations` | `ObservationResponse` | Filterable, paginated 5-minute CGM telemetry |
| **Predictions (Mode A)**| `GET /api/patients/{id}/predictions` | `HistoricalPredictionResponse` | Saved out-of-fold cross-validated prediction records |
| **Predictions (Mode B)**| `POST /api/predictions` | `InferenceResponse` | Real-time forward inference using champion models |
| **Personalisation Lab** | `GET /api/models/personalisation` | `PersonalisationResponse` | Authoritative Platt scaling personalisation audit metrics |
| **Model Evaluation** | `GET /api/models/evaluation?task={task}`| `EvaluationResponse` | Multi-model benchmark metrics (pooled and macro-averaged) |

---

## 3. Mode A vs. Mode B Scientific Separation

The frontend strictly enforces the distinction between two inference modes:

```
               ┌────────────────────────────────────────────────────────┐
               │                     GlycoTwin API                      │
               └───────────────┬────────────────────────┬───────────────┘
                               │                        │
               ┌───────────────▼────────┐      ┌────────▼───────────────┐
               │         MODE A         │      │         MODE B         │
               │  Retrospective OOF     │      │   Forward Deployment   │
               │  Predictions Endpoint  │      │   Inference Endpoint   │
               │  GET /api/patients/... │      │  POST /api/predictions │
               └───────────────┬────────┘      └────────┬───────────────┘
                               │                        │
               ┌───────────────▼────────┐      ┌────────▼───────────────┐
               │ Evaluates historical   │      │ Evaluates live 28-dim  │
               │ held-out cross-val     │      │ feature vectors on the │
               │ records with saved     │      │ champion model in      │
               │ ground-truth labels    │      │ simulated clinical     │
               │ for model calibration  │      │ operational contexts   │
               └────────────────────────┘      └────────────────────────┘
```

1. **Mode A (`GET /api/patients/{id}/predictions`)**:
   - Fetches true out-of-fold predictions produced during 5-fold cross-validation.
   - Includes cross-validation fold IDs, predicted probabilities, operational thresholds, and retrospectively observed ground-truth outcomes.
2. **Mode B (`POST /api/predictions`)**:
   - Accepts a real-time feature vector adhering to the 28-feature manifest.
   - Validates that target-derived leakage columns are strictly absent.
   - Enforces Task B preconditions: Rejects requests where `glucose_current < 70` with HTTP 422.

---

## 4. Query Parameter Builders & Pagination

To ensure responsive rendering across large clinical time-series:
- `getPatientObservations(patientId, { limit, offset, start_time, end_time })`: Safely encodes timestamps and limits (defaulting to 300 points or ~24 hours).
- `getPatientPredictions(patientId, { task, model, limit, offset })`: Retrieves chronologically sequenced prediction records without overflowing memory.

---

## 5. Error Handling & Fallback Behaviour

- `ApiError` class extracts structured error messages returned in FastAPI's `{ "detail": "..." }` responses.
- Reusable `ErrorAlert` component surfaces actionable error messages and provides a retry button.
- Clean `LoadingSkeleton` and `EmptyState` components provide feedback during asynchronous fetches.
