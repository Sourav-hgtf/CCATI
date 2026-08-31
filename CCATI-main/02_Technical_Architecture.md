# Technical Architecture Document
## Telecom Customer Churn Analysis & Segmentation Platform

**Version:** 1.0

---

## 1. Architecture Overview

```
                     USER
                      │
                      ▼
         ┌─────────────────────────┐
         │        FRONTEND         │
         │  React + TypeScript     │
         │  Tailwind CSS           │
         │  shadcn/ui              │
         │  Recharts / ECharts     │
         │  React Query            │
         │  React Router           │
         └────────────┬────────────┘
                      │ REST API (JSON, HTTPS)
                      ▼
         ┌─────────────────────────┐
         │         BACKEND         │
         │  FastAPI                │
         │  Pydantic                │
         │  Python                 │
         └────────────┬────────────┘
                      │
           ┌──────────┴───────────┐
           ▼                      ▼
  ┌─────────────────┐    ┌──────────────────┐
  │   ML ENGINE      │    │ BUSINESS ENGINE  │
  │  Scikit-learn    │    │ Risk scoring     │
  │  Pandas          │    │ Priority         │
  │  NumPy           │    │ Retention        │
  │  SHAP            │    │ ROI              │
  │  K-Means         │    │ Recommendations  │
  └────────┬─────────┘    └────────┬─────────┘
           │                       │
           └──────────┬────────────┘
                      ▼
              ┌───────────────┐
              │ DATA / MODELS │
              │  PostgreSQL   │
              │  Model Registry│
              │  Parquet      │
              └───────────────┘
```

## 2. Component Breakdown

### 2.1 Frontend
| Layer | Tech | Purpose |
|---|---|---|
| UI Framework | React + TypeScript | Type-safe component architecture |
| Styling | Tailwind CSS | Utility-first styling, design consistency |
| Component Library | shadcn/ui | Accessible, composable base components |
| Charts | Recharts / ECharts | Recharts for standard charts (trend lines, bars); ECharts for the cluster scatter plot (better perf for larger point counts + custom interactions) |
| Data Fetching/Caching | React Query | Server-state cache, polling for model metrics, optimistic UI |
| Routing | React Router | Client-side navigation (Dashboard / Customers / Segments / Model Monitoring) |

**Communication:** Frontend talks to Backend exclusively via REST (JSON over HTTPS). No direct DB or ML engine access from the client.

### 2.2 Backend (API Layer)
- **FastAPI** serves as the single entry point for all client requests and orchestrates calls to the ML Engine and Business Engine.
- **Pydantic** models enforce request/response schema validation and provide auto-generated OpenAPI docs.
- Responsibilities:
  - Auth/session validation (delegates to Security layer — see Security & Access doc).
  - Request routing to ML Engine (scoring, explanation, clustering) or Business Engine (risk/ROI/recommendation).
  - Aggregation: combines ML output + business rules into a single response payload for the frontend.
  - Pagination, filtering, and sorting logic for customer list endpoints.
  - Triggering/monitoring of async batch jobs (scoring runs, retraining) — status polling endpoints.

### 2.3 ML Engine
- **Scikit-learn**: preprocessing pipelines, classification models (Logistic Regression baseline, Random Forest/Gradient Boosting as candidates), K-Means clustering.
- **Imbalanced-learn (SMOTE)**: applied only within the training pipeline (fit on training fold only, never on validation/test/inference data) to address class imbalance.
- **Pandas/NumPy**: feature engineering (usage trend deltas, rolling windows, call-frequency aggregates).
- **SHAP**: post-hoc explainability, generating per-customer feature attribution values consumed by the frontend detail view.
- **K-Means**: clustering at-risk customers into segments; elbow/silhouette method for k selection, cluster labels persisted for the Business Engine and Frontend.
- Runs as a service/module invoked by the Backend (in-process for v1, or as a separate internal microservice if scaling requires it — see §5).

### 2.4 Business Engine
- **Risk scoring**: combines ML churn probability with Customer Lifetime Value (CLV) into a composite priority score.
- **Priority ranking**: sorts customers/segments by (risk × value) for retention team focus.
- **ROI engine**: estimates cost of a retention action vs. expected revenue saved, per customer/segment.
- **Recommendation rules**: rules/lookup mapping (segment profile + risk tier) → suggested retention action.
- Implemented as plain Python business-logic modules — deterministic, testable, versioned independently of ML models (so business rules can change without retraining).

### 2.5 Data / Models Layer
| Store | Purpose |
|---|---|
| **PostgreSQL** | System of record: customers, usage records, call logs, computed risk scores, segment assignments, recommendation history, audit logs |
| **Model Registry** | Versioned ML model artifacts + metadata (training date, hyperparameters, metrics, feature schema) — e.g., a simple registry table + object storage for `.pkl`/`.joblib` files, or MLflow if operational maturity requires it |
| **Parquet** | Columnar storage for large historical usage/feature datasets used in training and batch scoring (cheaper and faster than row-based DB reads for bulk ML workloads) |

## 3. Data Flow

### 3.1 Training Flow (offline/batch)
1. Raw usage + call-log data land in Parquet (from source systems / ETL).
2. Feature engineering pipeline (Pandas) builds the training feature set.
3. Train/test split (stratified on churn label).
4. SMOTE applied to training split only.
5. Model trained (Scikit-learn), evaluated (Precision/Recall/ROC-AUC/PR-AUC/confusion matrix).
6. If metrics pass promotion threshold, model + metadata registered in Model Registry.
7. K-Means fit on relevant customer feature space; cluster centroids stored.

### 3.2 Scoring Flow (scheduled batch, e.g. nightly/weekly)
1. Backend triggers a scoring job.
2. ML Engine loads latest promoted model from Model Registry.
3. Computes churn probability + SHAP values for each active customer.
4. Assigns cluster/segment label per customer.
5. Business Engine computes risk score, priority, ROI, and recommendation.
6. Results written to PostgreSQL (customer risk table).

### 3.3 Request Flow (online, user-facing)
1. Frontend requests customer list/detail/segment data via REST.
2. FastAPI reads pre-computed results from PostgreSQL (no live model inference in the request path — keeps API latency low).
3. Backend assembles response (Pydantic-validated) and returns to Frontend.
4. React Query caches and renders via Recharts/ECharts.

## 4. API Design Principles

- RESTful resource-oriented endpoints, e.g.:
  - `GET /api/customers` (paginated, filterable, sortable)
  - `GET /api/customers/{id}` (detail incl. SHAP + recommendation)
  - `GET /api/segments`
  - `GET /api/segments/{id}`
  - `GET /api/models/metrics`
  - `POST /api/scoring-jobs` (trigger, admin-only)
  - `GET /api/export/customers` (CSV export)
- All responses typed via Pydantic schemas; OpenAPI/Swagger auto-generated for contract clarity between FE/BE teams.
- Errors follow a consistent JSON error envelope (`code`, `message`, `details`).

## 5. Scalability & Deployment Notes

- v1: Backend, ML Engine, and Business Engine can run as a single FastAPI process (modules, not separate services) — simplest to operate.
- If dataset/customer volume grows significantly: split ML scoring into a separate worker/service (e.g., queued jobs via Celery/RQ or a simple cron) so heavy batch scoring doesn't block API responsiveness.
- Model Registry can start as a metadata table + filesystem/object storage; migrate to MLflow if multiple models/experiments need tracking at scale.
- Horizontal scaling of FastAPI is straightforward (stateless API instances behind a load balancer) since inference is precomputed, not on the request path.

## 6. Environments

| Environment | Purpose |
|---|---|
| Dev | Local development, sample/synthetic data |
| Staging | Full pipeline validation with anonymized production-like data |
| Production | Live data, scheduled scoring jobs, monitored SLAs |

## 7. Monitoring & Observability

- Model performance metrics logged per scoring run (stored in PostgreSQL, visualized in the Model Monitoring frontend view).
- Data drift checks (feature distribution comparison between training and current scoring batch) — flagged if drift exceeds threshold.
- API-level logging/metrics (request latency, error rate) via standard FastAPI middleware + logging stack of choice.
