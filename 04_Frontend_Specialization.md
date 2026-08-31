# Frontend Specialization Document
## Telecom Customer Churn Analysis & Segmentation Platform

**Version:** 1.0

---

## 1. Tech Stack Rationale

| Tech | Why |
|---|---|
| React + TypeScript | Type safety across API contracts (matches Pydantic schemas), scalable component architecture |
| Tailwind CSS | Fast, consistent utility-first styling; avoids CSS drift across a data-dense app |
| shadcn/ui | Accessible, unstyled-by-default primitives (tables, dialogs, dropdowns, tabs) that compose well with Tailwind, avoids reinventing common UI patterns |
| Recharts | Simple declarative charts for standard visualizations (line/bar/area trend charts, KPI sparklines) |
| ECharts | Used specifically for the cluster scatter plot and any dense/interactive visualization (better performance at higher point counts, built-in zoom/brush/tooltip interactions needed for cluster exploration) |
| React Query | Server-state caching, background refetch for near-real-time model metrics, request de-duplication, built-in loading/error states |
| React Router | Client-side routing across the app's core sections |

## 2. Information Architecture (Routes)

```
/                     → Dashboard (KPI overview)
/customers            → At-Risk Customer List
/customers/:id        → Customer Detail
/segments             → Segment Overview (cluster scatter + cards)
/segments/:id         → Segment Detail
/model-monitoring      → Model Performance & Drift
/admin                → User/Role Management, Scoring Job Triggers (Admin only)
```

## 3. Page-Level Specifications

### 3.1 Dashboard (`/`)
**Purpose:** At-a-glance churn health for the organization.

- KPI cards (shadcn `Card`): Overall churn rate, Revenue at risk, # High-priority customers, Model health badge (e.g., "Recall: 0.78 ✅").
- Trend chart (Recharts `LineChart`): churn rate over time (monthly).
- Revenue-at-risk breakdown (Recharts `BarChart`): by plan tier or region.
- "Top segments by risk" mini list linking to `/segments`.
- Loading state: skeleton cards (shadcn `Skeleton`) while React Query fetches.

### 3.2 At-Risk Customer List (`/customers`)
**Purpose:** Actionable, sortable/filterable list for retention managers.

- Data table (shadcn `Table` + `DataTable` pattern) with columns: Customer ID (masked PII), Plan, Tenure, Risk Score (visual badge: High/Med/Low), Usage Trend (mini sparkline via Recharts), Last Call Reason, Recommended Action.
- Filters (shadcn `Select`/`Popover`): risk tier, plan type, segment, date range.
- Search input (debounced) for customer ID lookup.
- Pagination (server-side, driven by React Query + API `page`/`page_size` params).
- Row click → navigates to `/customers/:id`.
- Bulk export button (role-gated: Retention Manager/Admin only) → triggers CSV export endpoint.
- Empty/error states explicitly designed (not just blank tables).

### 3.3 Customer Detail (`/customers/:id`)
**Purpose:** Deep-dive on one customer for a retention decision.

- Header: masked identifier, plan, tenure, risk badge, priority score.
- SHAP explanation panel: horizontal bar chart (Recharts) of top contributing features (positive = pushes toward churn, negative = pushes toward retention), color-coded.
- Usage/call-log trend chart (Recharts `AreaChart`/`LineChart`): usage over recent months with call-log events annotated as markers.
- Recommendation card: suggested retention action + estimated ROI, with a "Mark as actioned" control (writes back to Business Engine/DB via API — role-gated).
- PII reveal control: name/phone hidden by default behind a "Reveal" action, gated by role and logged (per Security & Access doc).

### 3.4 Segment Overview (`/segments`)
**Purpose:** Visualize and understand K-Means clusters.

- **Cluster scatter plot (ECharts)**: 2D projection (e.g., PCA/t-SNE components) of customers, colored by cluster; interactive zoom/brush/tooltip on hover (shows mini customer summary).
- Segment cards (shadcn `Card` grid) below/beside the plot: one per cluster, showing cluster size, avg tenure, avg usage drop-off %, dominant call-log reason, avg churn probability, suggested strategy label.
- Click a card → highlights that cluster in the scatter plot AND navigates to `/segments/:id` for full detail.

### 3.5 Segment Detail (`/segments/:id`)
- Full cluster profile: feature distributions (Recharts histograms/box-plot-style bars) vs. overall population.
- List of customers in this segment (reuses the customer table component, filtered).
- Recommended retention strategy narrative + ROI estimate for treating the whole segment.

### 3.6 Model Monitoring (`/model-monitoring`)
**Purpose:** ML/Analyst-facing performance and health view.

- Metrics over time (Recharts multi-line chart): Precision, Recall, ROC-AUC, PR-AUC per scoring/training run.
- Confusion matrix (custom small component, shadcn `Table`-based, color-scaled cells).
- Feature importance / drift indicator table: feature name, importance rank, drift flag (badge: stable/drifting).
- "Trigger scoring job" / "Trigger retraining" buttons (Admin/Analyst only), with job status polling via React Query (`refetchInterval`).

### 3.7 Admin (`/admin`)
- User/role table (shadcn `Table` + `Dialog` for edit).
- Audit log viewer (filterable by actor, action type, date).
- Scoring job history with status.

## 4. Component Library Structure

```
/src
  /components
    /ui              → shadcn primitives (button, table, card, dialog, badge, skeleton...)
    /charts
      TrendLineChart.tsx        (Recharts)
      RiskBarChart.tsx          (Recharts)
      SHAPExplanationChart.tsx  (Recharts)
      ClusterScatterPlot.tsx    (ECharts)
    /customer
      CustomerTable.tsx
      CustomerRiskBadge.tsx
      CustomerDetailHeader.tsx
      RecommendationCard.tsx
    /segments
      SegmentCard.tsx
      SegmentDetailPanel.tsx
    /monitoring
      ConfusionMatrix.tsx
      MetricsTrendChart.tsx
      DriftIndicatorTable.tsx
  /pages
    Dashboard.tsx
    Customers.tsx
    CustomerDetail.tsx
    Segments.tsx
    SegmentDetail.tsx
    ModelMonitoring.tsx
    Admin.tsx
  /hooks
    useCustomers.ts       (React Query wrapper)
    useCustomerDetail.ts
    useSegments.ts
    useModelMetrics.ts
    useAuth.ts            (role/session context)
  /lib
    apiClient.ts          (typed fetch wrapper, generated from OpenAPI schema where possible)
    formatters.ts         (currency, percentage, date formatting)
  /routes
    router.tsx            (React Router config incl. role-based route guards)
```

## 5. Design System Notes

- **Color semantics** (consistent across the app):
  - Risk High = red/destructive tone (shadcn `destructive` variant)
  - Risk Medium = amber/warning tone
  - Risk Low = green/success tone
  - Neutral/informational = slate/gray
- **Typography:** Tailwind default scale; data-dense tables use a slightly smaller base size (`text-sm`) with clear header weight (`font-medium`) for scan-ability.
- **Density:** This is a data-heavy internal tool — prioritize information density and scan-ability over decorative whitespace, while still respecting shadcn/Tailwind spacing tokens for consistency.
- **Accessibility:** All interactive elements keyboard-navigable (inherited from shadcn/Radix primitives); charts include accessible summary text/table fallback where feasible; color is never the only signal for risk tier (also use icon/label).
- Refer to the project's `frontend-design` guidance for deeper visual-direction principles (avoiding generic/templated defaults) when implementing final styling.

## 6. State Management Strategy

- **Server state** (customers, segments, metrics): React Query — handles caching, background refresh, retry, loading/error states. No Redux needed for server data.
- **Client/UI state** (filters, selected row, modal open/close): local component state or lightweight context; avoid global state libraries unless cross-page UI state sharing becomes a real need.
- **Auth/role state**: React Context (`useAuth`), populated post-SSO, consumed by route guards and role-gated UI controls.

## 7. API Contract Alignment

- Frontend TypeScript types should be generated/derived from the backend's Pydantic/OpenAPI schema (e.g., via `openapi-typescript`) to avoid FE/BE contract drift.
- All table/list endpoints assume server-side pagination, filtering, and sorting (never fetch-all-then-filter-client-side for the customer list, given expected data volume).

## 8. Performance Considerations

- Virtualize long tables (customer list) if row count per page is large, or rely on strict server-side pagination (preferred for v1 simplicity).
- Debounce search/filter inputs (300ms) before firing API requests.
- Lazy-load route-level code splitting (`React.lazy` + `Suspense`) for heavier pages (Segments' ECharts bundle, Model Monitoring).
- Memoize expensive chart data transforms (`useMemo`) especially for the cluster scatter plot dataset.
