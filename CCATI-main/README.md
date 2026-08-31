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

- `backend/` — FastAPI REST API, Pydantic validation models, RBAC authorization guards, security headers, correlation ID tracking, and endpoints (`/api/v1/customers`, `/api/v1/predict`, `/api/v1/segments`, `/api/v1/monitoring`, `/api/v1/export`, `/health`, `/ready`).
- `ml_engine/` — Scikit-learn pipelines: synthetic data generator, batch feature engineering, SMOTE-balanced training, model evaluation, SHAP explainability, K-Means clustering, statistical data drift engine (PSI / KS-test), and production performance evaluator.
- `business_engine/` — Composite risk scoring ($\text{Churn Prob} \times \text{CLV}$), retention ROI calculator, and centralized action rules configuration (`rules_config.yaml`).
- `frontend/` — React + TypeScript web app (TanStack Query, Tailwind CSS, Lucide icons, Recharts).
- `data/` — Storage directories for raw inputs (`raw/`), processed features (`processed/`), SQLite database (`database/`), and registered model artifacts (`models/`).
- `tests/` — Comprehensive test suite with 130+ unit, integration, RBAC, ML, drift, performance monitoring, and security tests.
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
| **Admin** | Full system control: model promotion, scoring triggers, and system audit log inspection. |

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

---

## 🚀 Quick Start & Development

### 1. Backend & ML Setup
```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Run FastAPI server
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

---

## 🩺 Health & Readiness Probes

- **Liveness Probe** (`GET /health`): Validates runtime responsiveness and active model artifact integrity.
- **Readiness Probe** (`GET /api/v1/ready`): Validates SQLite database connection, model registry metadata, and artifact checksums. Returns HTTP 200 when ready, HTTP 503 when degraded.

---

## 🧪 Testing & Quality Assurance

Run the complete test suite across ML pipelines, business engine, security matrix, drift detection, and performance evaluation:

```bash
# Run all automated tests
pytest -v

# Run security & production hardening tests only
pytest tests/test_security_and_hardening.py -v

# Frontend TypeScript check and Vite production build
cd frontend
npm run build
```

---

## 🔄 CI/CD Pipeline

The GitHub Actions CI workflow (`.github/workflows/ci.yml`) automatically executes on every push and pull request:
1. **Python Syntax Validation**: Compiles backend and ML source code (`py_compile`).
2. **Automated Testing**: Executes the full 131+ test suite under Python 3.14 with dependency caching.
3. **Frontend Verification**: Installs Node packages, performs TypeScript type validation (`tsc`), and executes Vite production bundling.
