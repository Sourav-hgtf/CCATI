# Feature Ticket List
## Telecom Customer Churn Analysis & Segmentation Platform

**Version:** 1.0
**Format:** Epic → Tickets (ID, Title, Description, Acceptance Criteria, Est.)

---

## EPIC 1 — Data Ingestion & Feature Engineering

### TICKET-101: Batch ingestion pipeline for usage & call-log data
- **Description:** Build a scheduled job to ingest raw usage records and customer service call logs from source files (CSV/Parquet) into PostgreSQL/Parquet storage.
- **Acceptance Criteria:**
  - Job runs on a schedule (daily/weekly, configurable).
  - Handles missing/malformed rows without failing the whole batch.
  - Ingestion run logged with row counts and error summary.
- **Estimate:** 5 pts

### TICKET-102: Feature engineering pipeline (usage trend & call features)
- **Description:** Compute derived features: usage drop-off deltas, rolling averages, call frequency, tenure buckets, recharge trend.
- **Acceptance Criteria:**
  - Feature set documented with definitions.
  - Pipeline output validated against a sample of manually computed values.
  - Output stored in Parquet for training and PostgreSQL for scoring.
- **Estimate:** 8 pts

### TICKET-103: Data quality checks & schema validation
- **Description:** Add automated checks (nulls, type mismatches, out-of-range values) before data enters the training/scoring pipeline.
- **Acceptance Criteria:**
  - Pipeline halts/flags on critical schema violations.
  - Data quality report generated per ingestion run.
- **Estimate:** 3 pts

---

## EPIC 2 — ML Engine: Classification Model

### TICKET-201: Train/test split with stratification
- **Description:** Implement stratified train/test split preserving churn class ratio.
- **Acceptance Criteria:** Split ratio configurable; class distribution verified in both sets.
- **Estimate:** 2 pts

### TICKET-202: SMOTE integration for class imbalance
- **Description:** Apply SMOTE (imbalanced-learn) to the training fold only within the pipeline.
- **Acceptance Criteria:**
  - SMOTE never applied to validation/test/inference data (unit test enforces this).
  - Configurable oversampling ratio.
- **Estimate:** 3 pts

### TICKET-203: Baseline model — Logistic Regression
- **Description:** Train and evaluate a baseline Logistic Regression classifier.
- **Acceptance Criteria:** Model trained, Precision/Recall/ROC-AUC/PR-AUC logged.
- **Estimate:** 3 pts

### TICKET-204: Candidate models — Random Forest / Gradient Boosting
- **Description:** Train and compare Random Forest and Gradient Boosting (e.g., XGBoost) against baseline.
- **Acceptance Criteria:** Comparison report with all metrics; best model flagged.
- **Estimate:** 5 pts

### TICKET-205: Model evaluation & reporting module
- **Description:** Build a reusable evaluation module producing Precision, Recall, F1, ROC-AUC, PR-AUC, and confusion matrix.
- **Acceptance Criteria:** Report generated as structured JSON consumable by API/frontend.
- **Estimate:** 3 pts

### TICKET-206: SHAP explainability integration
- **Description:** Generate per-customer SHAP values for the promoted model.
- **Acceptance Criteria:**
  - Top-N contributing features returned per customer.
  - Explanation values persisted alongside risk score.
- **Estimate:** 5 pts

### TICKET-207: Model registry (versioning & metadata)
- **Description:** Implement a model registry storing model artifacts + metadata (training date, metrics, feature schema, version).
- **Acceptance Criteria:**
  - Models retrievable by version.
  - "Current production model" flag supported.
- **Estimate:** 5 pts

---

## EPIC 3 — ML Engine: Segmentation

### TICKET-301: Feature scaling & preparation for clustering
- **Description:** Prepare and scale features for K-Means input (standardization).
- **Acceptance Criteria:** Scaler persisted for consistent inference-time transformation.
- **Estimate:** 2 pts

### TICKET-302: K-Means clustering with elbow/silhouette k-selection
- **Description:** Implement K-Means clustering pipeline with automated/assisted k selection.
- **Acceptance Criteria:**
  - Elbow and silhouette plots generated during model development.
  - Chosen k documented with rationale.
- **Estimate:** 5 pts

### TICKET-303: Cluster profiling module
- **Description:** Compute per-cluster summary statistics (avg tenure, avg usage drop, dominant complaint type, avg churn probability).
- **Acceptance Criteria:** Profile output structured for direct frontend consumption.
- **Estimate:** 3 pts

### TICKET-304: Dimensionality reduction for visualization (PCA/t-SNE)
- **Description:** Generate 2D projection coordinates per customer for the frontend cluster scatter plot.
- **Acceptance Criteria:** Coordinates persisted alongside cluster label per scoring run.
- **Estimate:** 3 pts

---

## EPIC 4 — Business Engine

### TICKET-401: Risk scoring module (probability × CLV)
- **Description:** Combine churn probability with Customer Lifetime Value into a composite priority score.
- **Acceptance Criteria:** Scoring formula documented and configurable (weights).
- **Estimate:** 3 pts

### TICKET-402: ROI calculator for retention actions
- **Description:** Estimate cost vs. expected revenue saved for each recommended action, per customer/segment.
- **Acceptance Criteria:** ROI value returned alongside each recommendation.
- **Estimate:** 5 pts

### TICKET-403: Recommendation rules engine
- **Description:** Build rule/lookup logic mapping segment + risk tier → suggested retention action.
- **Acceptance Criteria:** Rules configurable without redeploying ML models; documented rule table.
- **Estimate:** 5 pts

---

## EPIC 5 — Backend API

### TICKET-501: FastAPI project scaffold & Pydantic schemas
- **Description:** Set up FastAPI app structure, base Pydantic models, OpenAPI docs.
- **Acceptance Criteria:** `/docs` renders correctly; base health-check endpoint live.
- **Estimate:** 3 pts

### TICKET-502: `GET /api/customers` (paginated, filterable, sortable)
- **Description:** Endpoint returning at-risk customer list with server-side pagination/filtering/sorting.
- **Acceptance Criteria:** Supports filters for risk tier, plan, segment, date range; response time < 500ms at target data volume.
- **Estimate:** 5 pts

### TICKET-503: `GET /api/customers/{id}` (detail incl. SHAP + recommendation)
- **Description:** Endpoint returning full customer detail payload.
- **Acceptance Criteria:** Includes risk score, SHAP top features, usage/call trend series, recommendation + ROI.
- **Estimate:** 5 pts

### TICKET-504: `GET /api/segments` and `GET /api/segments/{id}`
- **Description:** Endpoints for segment list (with scatter coordinates) and segment detail (profile + customer list).
- **Acceptance Criteria:** Response includes cluster profile stats and 2D projection coordinates.
- **Estimate:** 5 pts

### TICKET-505: `GET /api/models/metrics`
- **Description:** Endpoint returning model performance history for the monitoring dashboard.
- **Acceptance Criteria:** Returns time-series metrics + latest confusion matrix + drift flags.
- **Estimate:** 3 pts

### TICKET-506: `POST /api/scoring-jobs` (trigger + status polling)
- **Description:** Admin/Analyst-only endpoint to trigger a batch scoring run, plus a status endpoint for polling.
- **Acceptance Criteria:** Job status transitions (queued/running/succeeded/failed) visible via API; role-gated.
- **Estimate:** 5 pts

### TICKET-507: `GET /api/export/customers` (CSV export)
- **Description:** Export at-risk customer list as CSV, respecting current filters.
- **Acceptance Criteria:** Export action logged (per Security doc); role-gated to Retention Manager/Admin.
- **Estimate:** 3 pts

---

## EPIC 6 — Security & Access

### TICKET-601: SSO/OIDC integration
- **Description:** Integrate organizational SSO for authentication.
- **Acceptance Criteria:** Login redirects to IdP; session established post-auth; logout invalidates session.
- **Estimate:** 5 pts

### TICKET-602: RBAC middleware (role-gated endpoints)
- **Description:** Implement role-based permission checks at the API layer for all endpoints per the Security & Access document.
- **Acceptance Criteria:** Unauthorized role receives `403`; role matrix covered by tests.
- **Estimate:** 5 pts

### TICKET-603: PII masking & reveal-with-audit-log
- **Description:** Mask PII fields by default in list views; implement gated "reveal" action that logs access.
- **Acceptance Criteria:** Reveal action requires authorized role and writes an audit log entry.
- **Estimate:** 3 pts

### TICKET-604: Audit log storage & admin viewer
- **Description:** Persist audit events (PII reveal, exports, model promotion, config changes) and expose an admin-only viewer.
- **Acceptance Criteria:** Filterable by actor/action/date; append-only storage.
- **Estimate:** 5 pts

---

## EPIC 7 — Frontend: Dashboard & Customer Views

### TICKET-701: Dashboard KPI cards & trend chart
- **Description:** Build the main dashboard with KPI cards and churn-rate trend line (Recharts).
- **Acceptance Criteria:** Data-driven from `/api/models/metrics` and a dashboard summary endpoint; loading/error states implemented.
- **Estimate:** 5 pts

### TICKET-702: At-risk customer table with filters
- **Description:** Build the customer list page (shadcn Table, filters, search, pagination).
- **Acceptance Criteria:** Server-side pagination/filtering wired to `/api/customers`; masked PII displayed by default.
- **Estimate:** 8 pts

### TICKET-703: Customer detail view with SHAP chart
- **Description:** Build customer detail page including SHAP explanation bar chart and usage/call trend chart.
- **Acceptance Criteria:** Renders correctly for customers with varying feature counts; PII reveal control implemented per Security spec.
- **Estimate:** 8 pts

### TICKET-704: Recommendation card & "mark as actioned" flow
- **Description:** Display recommended action + ROI; allow marking an action as taken.
- **Acceptance Criteria:** Action state persisted via API; reflected in customer list/detail.
- **Estimate:** 5 pts

---

## EPIC 8 — Frontend: Segmentation & Monitoring

### TICKET-801: Cluster scatter plot (ECharts)
- **Description:** Build interactive 2D cluster scatter plot with zoom/brush/tooltip.
- **Acceptance Criteria:** Colored by cluster; tooltip shows customer summary on hover; performant at target data volume.
- **Estimate:** 8 pts

### TICKET-802: Segment cards & segment detail page
- **Description:** Build segment summary cards and the segment detail page (profile stats + filtered customer list).
- **Acceptance Criteria:** Clicking a card highlights the cluster in the scatter plot and links to detail page.
- **Estimate:** 5 pts

### TICKET-803: Model monitoring dashboard
- **Description:** Build metrics-over-time chart, confusion matrix component, and drift indicator table.
- **Acceptance Criteria:** Data-driven from `/api/models/metrics`; drift flags visually distinct.
- **Estimate:** 8 pts

### TICKET-804: Admin panel (users/roles, audit log, job history)
- **Description:** Build the admin page for user/role management, audit log viewing, and scoring job history.
- **Acceptance Criteria:** Role-gated to Admin only; audit log filterable.
- **Estimate:** 8 pts

---

## EPIC 9 — Cross-Cutting / DevOps

### TICKET-901: CI pipeline (lint, test, build) for frontend & backend
- **Estimate:** 5 pts

### TICKET-902: Environment configuration (dev/staging/prod)
- **Estimate:** 3 pts

### TICKET-903: OpenAPI-to-TypeScript type generation setup
- **Estimate:** 2 pts

### TICKET-904: Logging & basic observability (API latency, error rate)
- **Estimate:** 3 pts

### TICKET-905: Security review checklist pass before staging release
- **Estimate:** 3 pts

---

## Suggested Sprint Grouping (indicative, adjust to team velocity)

| Sprint | Focus |
|---|---|
| 1 | Epic 1 (Data Ingestion) + Epic 5 scaffold (501) |
| 2 | Epic 2 (Classification Model) |
| 3 | Epic 3 (Segmentation) + Epic 4 (Business Engine) |
| 4 | Epic 5 (remaining API endpoints) + Epic 6 (Security) |
| 5 | Epic 7 (Dashboard & Customer frontend) |
| 6 | Epic 8 (Segmentation & Monitoring frontend) + Epic 9 (DevOps hardening) |
