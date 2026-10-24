# GLYCOTWIN — BACKEND ARCHITECTURE & DESIGN

**Component:** Phase 3 FastAPI Backend & Model Serving Service  
**Author:** Lead Backend & Machine Learning Engineer  
**Status:** Implemented & Verified (73/73 Tests Passing)

---

## 1. Architectural Overview

The GlycoTwin backend is engineered as a high-performance, modular Python service using FastAPI, Pydantic v2, and scikit-learn/XGBoost. It bridges the verified HUPA-UCM clinical research dataset, the Phase 2 population and personalised machine learning models, and the upcoming Phase 4 React frontend.

```
                           +------------------------------------+
                           |    Client Application (React UI)   |
                           +-----------------+------------------+
                                             | HTTP / REST (JSON)
                                             v
                           +------------------------------------+
                           |        FastAPI Router Layer        |
                           |   /api/health      /api/metadata   |
                           |   /api/patients    /api/predictions|
                           |   /api/models/eval /api/models/pers|
                           +-----------------+------------------+
                                             | Dependency Injection
                                             v
+------------------------+ +------------------------+ +------------------------+
|      DataService       | |      ModelService      | |   EvaluationService    |
| - In-memory cache      | | - Model registry       | | - Phase 2 audit run    |
| - 309,392 observations | | - 28-feature validator | | - Population metrics   |
| - Precomputed profiles | | - Leakage guardrails   | | - Personalisation deltas|
| - Out-of-fold matrix   | | - Real-time inference  | | - Purge-gap stats      |
+-----------+------------+ +-----------+------------+ +-----------+------------+
            |                          |                          |
            v                          v                          v
+------------------------+ +------------------------+ +------------------------+
| data/processed/        | | artifacts/models/      | | artifacts/evaluation/  |
| glycotwin_features.    | | - logistic_regression  | | phase2_audit_run/      |
| parquet                | | - xgboost              | | - population_metrics   |
|                        | | - rule_based baseline  | | - participant_metrics  |
+------------------------+ +------------------------+ +------------------------+
```

---

## 2. Layered Component Responsibilities

### 2.1 API Presentation Layer (`backend/app/api/`)
- Validates query parameters and request bodies against strict Pydantic schemas.
- Dispatches business requests to injected singleton services.
- Emits standard HTTP status codes:
  - `200 OK`: Successful retrieval or model prediction.
  - `400 Bad Request`: Malformed task/model parameter combinations.
  - `404 Not Found`: Unknown participant ID or missing resource.
  - `422 Unprocessable Content`: Feature validation failure, missing features, leakage field detected, or Task B condition violated.
  - `503 Service Unavailable`: Model runtime artifact missing or uninitialized.

### 2.2 Service Layer (`backend/app/services/`)
- **`DataService`**: Loads `data/processed/glycotwin_features.parquet` (309,392 rows, 25 participants) once on application startup. Indexes records by `participant_id` and precomputes glycemic summary profiles (TIR, TBR, TAR, mean, std) in memory to achieve sub-millisecond response latencies.
- **`ModelService`**: Manages the deployment model registry. Loads trained scikit-learn Pipelines (`StandardScaler` + `LogisticRegression`) and XGBoost classifiers. Validates feature vectors against `FEATURE_COLUMNS`, checks numerical finiteness, enforces the Task B baseline condition ($g_t \ge 70.0\text{ mg/dL}$), and applies calibrated operational thresholds.
- **`EvaluationService`**: Ingests authoritative evaluation artifacts from `artifacts/evaluation/phase2_audit_run/`. Exposes both pooled and participant-balanced macro metrics for population models, and reports participant-level personalisation deltas with 30-minute purge gap metrics.

### 2.3 Dependency Injection (`backend/app/dependencies.py`)
- Provides decoupling and testability via FastAPI's `Depends` mechanism. Ensures singleton services are initialized and ready before serving route handlers.

### 2.4 Configuration & Path Resolution (`backend/app/config.py`)
- Resolves all filesystem paths dynamically relative to the repository root. Prohibits hard-coded local file paths.
- Centralizes verified operational decision thresholds and task aliases.

---

## 3. Data Integrity & In-Memory Performance

1. **Single-Pass Ingestion:** The 309,392-row dataset (~22 MB parquet on disk, ~85 MB in RAM) is loaded during the FastAPI `lifespan` startup event, eliminating repetitive disk I/O on HTTP queries.
2. **Deterministic Pagination:** Observations and historical predictions support `limit` and `offset` pagination with `total_items` and `total_pages` calculation.
3. **Immutability:** The data service performs non-destructive read-only queries, preserving the source parquet dataset intact.

---

## 4. Local Deployment & CORS Configuration

- Development server binds to `127.0.0.1:8000` by default.
- CORS middleware is configured strictly for local development origins (`http://localhost:5173`, `http://127.0.0.1:5173`, `http://localhost:3000`). Public wildcard CORS (`*`) is avoided.
