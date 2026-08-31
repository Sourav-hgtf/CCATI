# Telecom Customer Churn Analysis & Segmentation Platform

A web-based platform built with FastAPI, Scikit-learn, and React+TS that helps telecom retention teams identify subscribers at high risk of churn, explain predictions using SHAP, group subscribers into behavioral K-Means segments, and quantify the ROI of retention actions.

---

## 🏗️ Architecture Overview

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
              └────────────┬────────────┘
                           │ REST API (JSON)
                           ▼
              ┌─────────────────────────┐
              │         BACKEND         │
              │  FastAPI                │
              │  Pydantic               │
              │  Python 3.11+           │
              └────────────┬────────────┘
                           │
            ┌──────────────┴──────────────┐
            ▼                             ▼
   ┌─────────────────┐           ┌──────────────────┐
   │   ML ENGINE     │           │ BUSINESS ENGINE  │
   │  Scikit-learn   │           │ Risk scoring     │
   │  SMOTE          │           │ Priority ranking │
   │  SHAP           │           │ ROI calculator   │
   │  K-Means        │           │ Recommendation   │
   └────────┬────────┘           └────────┬─────────┘
            │                             │
            └──────────────┬──────────────┘
                           ▼
                   ┌───────────────┐
                   │ DATA / MODELS │
                   │  SQLite/Postgres│
                   │  Parquet      │
                   │  Model Registry│
                   └───────────────┘
```

---

## 📁 Repository Structure

- `backend/` — FastAPI REST application, Pydantic schemas, RBAC middleware, audit logging, endpoints (`/api/v1/customers`, `/api/v1/segments`, `/api/v1/models/metrics`, `/api/v1/scoring-jobs`, `/api/v1/export/customers`).
- `ml_engine/` — Scikit-learn pipelines: synthetic data generator, batch ingestion, feature engineering, SMOTE-balanced training, model evaluation, SHAP explainability, K-Means clustering & PCA 2D projections, model registry.
- `business_engine/` — Composite risk scoring (Churn Prob × CLV), retention ROI calculator, recommendation rules engine (`rules_config.yaml`).
- `frontend/` — React + TypeScript frontend web app (shadcn/ui, Recharts, ECharts).
- `data/` — Storage directories for raw files (`raw/`), processed features (`processed/`), SQLite database (`database/`), and registered model artifacts (`models/`).
- `tests/` — Comprehensive test suite for ML pipelines, business logic, RBAC, and API endpoints.

---

## 🚀 Quick Start & Installation

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ (for frontend)

### 2. Python Backend & ML Setup
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run full test suite
pytest
```

### 3. Running FastAPI Server
```bash
# Start backend local server
python -m uvicorn backend.app.main:app --reload --port 8000
```
Open API docs at: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🔑 Security & Role-Based Access Control (RBAC)

| Role | Permissions |
|---|---|
| **Executive** | Read-only access to KPIs and aggregated segment metrics. No PII detail access. |
| **RetentionManager** | Full access to customer list, detail view (gated PII reveal), retention actions, CSV exports. |
| **Analyst** | Access to model monitoring, feature importance, drift reports, batch scoring job triggers. |
| **Admin** | Full system control: user/role management, model promotion, audit log inspection, scoring jobs. |

---

## 🧪 Running Tests
```bash
# Run all unit and integration tests
pytest

# Test coverage breakdown
pytest --cov=ml_engine --cov=business_engine --cov=backend
```
