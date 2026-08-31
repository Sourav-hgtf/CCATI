# Product Requirements Document (PRD)
## Telecom Customer Churn Analysis & Segmentation Platform

**Version:** 1.0
**Status:** Draft
**Owner:** Product/Engineering

---

## 1. Overview

A web-based platform that helps telecom business teams identify subscribers at high risk of churn, understand *why* they're at risk, group them into actionable segments, and act on retention recommendations — all backed by a machine learning engine (classification + clustering) and a business rules engine (risk scoring, ROI, prioritization).

## 2. Problem Statement

Telecom operators lose significant recurring revenue to churn. Retention teams currently rely on lagging indicators (a customer has already cancelled) or blunt, one-size-fits-all retention campaigns. There is no unified tool that:
- Predicts churn risk *before* cancellation, using usage drop-off and customer service call patterns.
- Explains *why* a customer is flagged (model explainability).
- Groups at-risk customers into meaningful segments for targeted retention strategy.
- Quantifies the ROI of retention actions so limited budget is spent on the highest-value saves.

## 3. Goals & Non-Goals

### Goals
- Provide a dashboard where retention managers can see churn risk across the customer base.
- Surface a ranked, prioritized list of at-risk customers (risk score + business value).
- Explain each prediction using feature-level attribution (SHAP).
- Segment at-risk customers via K-Means clustering into behaviorally distinct groups.
- Recommend retention actions per customer/segment with estimated ROI.
- Allow filtering, drill-down, and export of at-risk customer lists.
- Track model performance over time (Precision, Recall, ROC-AUC, PR-AUC) given class imbalance.

### Non-Goals (v1)
- Automated execution of retention campaigns (e.g., auto-sending discount emails) — v1 only recommends.
- Real-time streaming scoring (v1 is batch/scheduled scoring).
- Multi-tenant SaaS support (v1 is single-organization deployment).
- Mobile app (web-responsive only).

## 4. Target Users / Personas

| Persona | Needs |
|---|---|
| **Retention Manager** | Prioritized list of at-risk high-value customers, ROI-ranked actions |
| **Data/ML Analyst** | Model performance monitoring, feature importance, retraining triggers |
| **Customer Service Lead** | Segment profiles tied to call-log patterns to adjust support workflows |
| **Executive/Ops** | High-level churn KPIs, trend over time, revenue-at-risk summary |

## 5. Key Use Cases

1. **View churn risk dashboard** — see overall churn rate, revenue at risk, model health at a glance.
2. **Explore at-risk customer list** — sortable/filterable table (risk score, plan, tenure, last call reason, usage trend).
3. **Drill into a customer profile** — see risk score, SHAP explanation, usage/call history trend chart, recommended action, estimated retention ROI.
4. **View customer segments** — K-Means cluster visualization (2D projection), cluster profiles (avg tenure, avg usage drop, dominant complaint type, churn probability), segment-level recommended strategy.
5. **Monitor model performance** — Precision/Recall/ROC-AUC/PR-AUC over time, confusion matrix, data drift indicators.
6. **Export/report** — export at-risk list (CSV) and segment summary for offline use by retention teams.

## 6. Functional Requirements

### 6.1 Data Ingestion
- Ingest customer usage records (call minutes, data usage, SMS, recharge/billing trend) and customer service call logs (call reason, frequency, sentiment/category, resolution status).
- Support scheduled batch ingestion (daily/weekly) from CSV/Parquet sources into PostgreSQL.

### 6.2 ML Engine
- Feature engineering pipeline (usage trend deltas, rolling averages, call frequency, tenure buckets).
- Class-imbalance handling via SMOTE (or variants) during training only (never applied to validation/test/inference data).
- Classification model(s) (e.g., Logistic Regression baseline, Random Forest/XGBoost candidate) producing churn probability per customer.
- Model evaluation using Precision, Recall, F1, ROC-AUC, PR-AUC — PR-AUC/Recall prioritized given imbalance.
- SHAP-based explainability per prediction (top contributing features).
- K-Means clustering of at-risk (or full) customer base; elbow/silhouette-based k selection.
- Model registry: versioned models with metadata (training date, metrics, feature set).

### 6.3 Business Engine
- Risk scoring: combine model probability with customer lifetime value (CLV) to produce a priority score.
- ROI calculator: estimated retention cost vs. estimated revenue saved per recommended action.
- Recommendation rules: map segment/risk profile → suggested retention action (e.g., loyalty discount, proactive support outreach, plan upgrade offer).

### 6.4 Backend API
- REST API (FastAPI) exposing: customer list/search, customer detail, segment list/detail, model metrics, recommendation retrieval, export endpoints.
- Pydantic schemas for strict request/response validation.

### 6.5 Frontend
- Dashboard (KPIs, trend charts).
- At-risk customer table (filter, sort, paginate, export).
- Customer detail view (risk breakdown, SHAP chart, history trend, recommendation).
- Segmentation view (cluster scatter plot, cluster profile cards).
- Model monitoring view (metrics over time, confusion matrix).

## 7. Success Metrics

| Metric | Target |
|---|---|
| Model Recall (churn class) | ≥ 0.75 |
| Model PR-AUC | ≥ 0.60 (baseline-dependent, track improvement) |
| Dashboard load time | < 2s for customer list (paginated) |
| Retention team adoption | ≥ 70% of flagged high-priority customers reviewed weekly |
| Revenue-at-risk visibility | 100% of at-risk customers surfaced with a recommendation |

## 8. Assumptions & Constraints

- Historical labeled churn data (churned vs. retained) is available for supervised training.
- Usage and call-log data can be joined on a common customer ID at a consistent time granularity (e.g., monthly).
- SMOTE and clustering are computationally feasible in batch (not real-time) given dataset size.
- Single organization/internal tool — auth is internal SSO, not public signup.

## 9. Open Questions

- What is the retraining cadence (weekly/monthly) and who approves promoting a new model to production?
- What defines "high value" customer for CLV weighting — plan tier, tenure, or predicted future revenue?
- Should clustering run on the full base or only on customers above a churn-probability threshold?
- Data retention policy for historical call logs (PII considerations — see Security & Access document).

## 10. Release Plan (Phased)

- **Phase 1 (MVP):** Data ingestion, baseline classification model, risk-scored customer table, basic dashboard.
- **Phase 2:** SHAP explainability, K-Means segmentation view, ROI-based recommendations.
- **Phase 3:** Model monitoring dashboard, scheduled retraining, export/reporting, drift alerts.
