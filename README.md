# Telecom Customer Churn Analysis & Segmentation Platform

An enterprise-grade, production-hardened web platform built with FastAPI, Scikit-learn, and React+TypeScript. The platform empowers telecom retention teams to identify subscribers at high risk of churn, explain predictions using TreeSHAP, segment subscribers into behavioral K-Means cohorts, quantify the ROI of retention offers, monitor real-time feature drift (PSI/KS-test), and track production model performance against ground truth.

---

## 🏗️ Architecture Overview

```
                          USER / CLIENT
                               │
                               ▼
               ┌──────────────────────────────┐
               │           FRONTEND           │
               │ React 18 + TypeScript + Vite │
               │ Tailwind CSS + Lucide Icons  │
               │ Recharts + TanStack Query    │
               └──────────────┬───────────────┘
                              │ REST API (HTTPS / JSON)
                              ▼
               ┌──────────────────────────────┐
               │           BACKEND            │
               │ FastAPI + Pydantic v2        │
               │ Security Headers (OWASP)     │
               │ RBAC + JWT Token Auth        │
               │ Request Correlation Tracing  │
               └──────────────┬───────────────┘
                              │
             ┌────────────────┴────────────────┐
             ▼                                 ▼
    ┌─────────────────┐               ┌──────────────────┐
    │    ML ENGINE    │               │ BUSINESS ENGINE  │
    │ Scikit-learn    │               │ Risk scoring     │
    │ SMOTE Pipelines │               │ CLV Priority     │
    │ TreeSHAP Expl.  │               │ ROI Calculator   │
    │ K-Means + PCA   │               │ Actions Engine   │
    │ Drift (PSI/KS)  │               │ Rules Config YAML│
    │ Perf. Evaluator │               └────────┬─────────┘
    └────────┬────────┘                        │
             │                                 │
             └────────────────┬────────────────┘
                              ▼
                    ┌───────────────────┐
                    │   DATA & MODELS   │
                    │ SQLite / Postgres │
                    │ Parquet Features  │
                    │ Model Registry    │
                    │ SHA-256 Verified  │
                    └───────────────────┘
```

---

## 📁 Repository Structure

- `backend/` — FastAPI REST API, Pydantic validation models, RBAC authorization guards, security headers, correlation ID tracking, audit logging, rate limiting, and endpoints for customers, predictions, segments, exports, data quality, model monitoring, and operations.
- `ml_engine/` — Scikit-learn pipelines for ingestion, Kaggle adapters, data-quality validation, feature engineering, SMOTE-balanced training, model evaluation, SHAP explainability, K-Means clustering, statistical data drift (PSI / KS-test), and production performance evaluation.
- `business_engine/` — Composite risk scoring ($\text{Churn Prob} \times \text{CLV}$), retention ROI calculator, and centralized action rules configuration (`rules_config.yaml`).
- `frontend/` — React + TypeScript web app with dashboard, predictions, analytics, segmentation, retention, ROI, model monitoring, data-quality, operations, reports, and admin views.
- `data/` — Storage directories for raw inputs and dataset registry (`raw/`), validated and engineered features (`processed/`), local SQLite database files (`database/`), and registered model artifacts (`models/`).
- `configs/datasets.yaml` — Centralized Kaggle source identifiers, canonical schema, quality thresholds, feature-engineering settings, training settings, and promotion thresholds.
- `docs/` — Dataset acquisition, versioning, schema validation, and feature-mapping documentation.
- `alembic/` — Database migrations, including the `customer_scores.created_at` migration required for time-based analytics.
- `tests/` — 287 pytest test functions covering unit, integration, RBAC, ML, drift, performance monitoring, migration, and security behavior.
- `.github/workflows/` — Automated CI pipeline for linting, syntax compilation, pytest suite, and frontend TypeScript/Vite builds.

---

## 🔒 Security & Production Hardening

### 1. OWASP Security Headers
Every backend response automatically includes:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: geolocation=(), camera=(), microphone=(), payment=()`

### 2. Request Correlation & Observability
- Every request is tagged with an `X-Correlation-ID` and `X-Request-ID` header.
- Duration tracking via `X-Process-Time-MS`.
- Structured JSON logging ensures zero PII or credentials leak into server logs.

### 3. Payload & Error Protection
- Maximum request entity size protection ($10\text{ MB}$ limit) returning HTTP 413 on oversized payloads.
- Standardized API error responses hiding internal stack traces, file paths, and database details.

### 4. Role-Based Access Control (RBAC)

| Role | Permissions |
|---|---|
| **Executive** | Read-only access to high-level KPIs, churn trends, and aggregated segment metrics. No PII access. |
| **RetentionManager** | Customer workspace, detailed subscriber profiles (gated PII reveal), retention action assignment, and CSV export. |
| **Analyst** | Model monitoring, data drift intelligence, performance evaluations, and batch scoring job triggers. |
| **ModelManager** | Model registry and model lifecycle operations, including promotion workflows. |
| **Operations** | Operational prediction workflows and service monitoring. |
| **Viewer** | Read-only access to permitted dashboards and monitoring views. |
| **Admin** | Full system control: user and role administration, model promotion, scoring triggers, and audit log inspection. |

### 5. Model Artifact Security & Integrity
- Model artifacts are loaded strictly from the verified project registry path.
- Cryptographic SHA-256 checksums validate artifact integrity prior to inference, failing safely if corrupted.

---

## ⚙️ Environment Configuration

Copy `.env.example` to `.env` for local customization:

```bash
cp .env.example .env
```

### Key Environment Variables

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | Environment mode (`development`, `production`, `testing`). |
| `DEBUG` | `false` | Enable debug logging. Always `false` in production. |
| `SECRET_KEY` | *(Configurable)* | Cryptographically secure 32+ char key for JWT signing. |
| `ALLOWED_ORIGINS` | `http://localhost:5173,...` | Comma-separated list of allowed CORS domains. |
| `DATABASE_URL` | `sqlite:///data/database/telecom_churn.db` | SQLAlchemy / SQLite database connection URI. |
| `VITE_API_URL` | `http://localhost:8000` | Backend API base URL for frontend requests. |
| `KAGGLE_USERNAME` | *(Required for Kaggle downloads)* | Kaggle username or service-account username. |
| `KAGGLE_KEY` | *(Required for Kaggle downloads)* | Kaggle API key. Keep it in the environment or `~/.kaggle/kaggle.json`; never commit it. |
| `ENABLE_AUDIT_LOGGING` | `true` | Enable structured audit events. |
| `ENABLE_METRICS` | `true` | Enable in-memory operational metrics at `/api/v1/metrics`. |

For PostgreSQL development, set `DATABASE_URL` to a PostgreSQL SQLAlchemy URI such as `postgresql+psycopg://postgres:<password>@localhost:5432/telecom_churn`. The default Compose database is PostgreSQL 15.

---

## 🚀 Quick Start & Development

### 1. Backend & ML Setup
```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Apply database migrations when using an existing database
alembic upgrade head

# 4. Run FastAPI server
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```
API Documentation available at: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev -- --host --port 5173
```
Frontend Web Dashboard: [http://localhost:5173](http://localhost:5173)

### 3. Docker Compose

To run the backend, frontend, and PostgreSQL service together:

```bash
docker compose up --build
```

The dashboard is available at [http://localhost:3000](http://localhost:3000), the API at [http://localhost:8000](http://localhost:8000), and PostgreSQL at `localhost:5432`.

### 4. Kaggle Dataset Integration

TASK-21 supports the Cell2Cell and IBM Telco Customer Churn datasets. Configure credentials without committing them:

```bash
export KAGGLE_USERNAME=<your_kaggle_username>
export KAGGLE_KEY=<your_kaggle_api_key>
```

Or use the standard local file at `~/.kaggle/kaggle.json`. Dataset downloads are handled by `ml_engine/pipelines/kaggle_download.py`, then adapters map source columns to the canonical schema. Each raw dataset is registered with row counts, source metadata, and a SHA-256 checksum in `data/raw/dataset_registry.json`. See [docs/DATASET.md](docs/DATASET.md) and [docs/FEATURE_MAPPING.md](docs/FEATURE_MAPPING.md) for the ingestion and mapping details.

---

## 🩺 Health & Readiness Probes

- **Liveness Probe** (`GET /health`): Validates runtime responsiveness and active model artifact integrity.
- **Readiness Probe** (`GET /api/v1/ready`): Validates the configured database connection, model registry metadata, and artifact checksums. Returns HTTP 200 when ready, HTTP 503 when degraded.

## 📊 Monitoring & Operations

The Model Monitor workspace exposes four operational views:

- **Model Performance** — Precision, recall, F1, ROC-AUC, PR-AUC, confusion matrix, baseline deltas, and evaluation history against labeled production records.
- **Data Drift Intelligence** — PSI-based numerical and categorical drift analysis, severity, affected features, recommendations, and scan history.
- **Data Quality & Validation** — Record quality scores, invalid and duplicate counts, field-level issues, and pre-inference validation results.
- **Operations** — API and prediction latency, error rates, request counters, model-load metrics, drift alerts, and filterable audit events.

Monitoring endpoints include `GET /api/v1/monitoring/performance`, `GET /api/v1/monitoring/status`, `GET /api/v1/data-quality`, and `GET /api/v1/metrics`. Scan and promotion endpoints remain protected by RBAC and rate limits.

---

## 🧪 Testing & Quality Assurance

Run the complete test suite across ML pipelines, business engine, security matrix, drift detection, and performance evaluation:

```bash
# Run all automated tests (287 test functions currently)
pytest -v

# Run security & production hardening tests only
pytest tests/test_security_and_hardening.py -v

# Run dataset integration and monitoring tests
pytest tests/test_kaggle_integration.py tests/test_model_monitoring_and_drift.py -v

# Frontend TypeScript check and Vite production build
cd frontend
npm run build
```

---

## 🔄 CI/CD Pipeline

The GitHub Actions CI workflow (`.github/workflows/ci.yml`) automatically executes on every push and pull request:
1. **Python Syntax Validation**: Compiles backend and ML source code (`py_compile`).
2. **Automated Testing**: Executes the full pytest suite under Python 3.14 with dependency caching.
3. **Frontend Verification**: Installs Node packages, performs TypeScript type validation (`tsc`), and executes Vite production bundling.
