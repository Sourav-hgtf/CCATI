# Security & Access Document
## Telecom Customer Churn Analysis & Segmentation Platform

**Version:** 1.0

---

## 1. Purpose

This document defines authentication, authorization, data protection, and compliance controls for the platform, given that it processes sensitive customer data (usage records, service call logs, and derived churn predictions).

## 2. Data Classification

| Data Type | Classification | Notes |
|---|---|---|
| Customer ID (internal, non-PII key) | Internal | Used for joins; not directly identifying on its own |
| Customer name, phone number, address | **PII — Restricted** | Must be masked/tokenized outside of authorized detail views |
| Usage records (call minutes, data usage, recharge history) | Confidential | Business-sensitive, customer-behavior data |
| Customer service call logs (reason, transcript/summary, sentiment) | **Sensitive — Restricted** | May contain PII or complaint content; treat as high sensitivity |
| Churn probability / risk score | Confidential | Derived business intelligence |
| SHAP explanations | Confidential | Derived, tied to individual customer record |
| Aggregated segment profiles | Internal | Not tied to a single identifiable customer once aggregated |
| Model artifacts / weights | Confidential | Intellectual property + potential re-identification risk if exposed |

## 3. Authentication

- **Internal SSO (SAML/OIDC)** integration with the organization's identity provider — no standalone username/password signup for v1 (internal tool, not public-facing).
- Session tokens (JWT or server-side session) issued after SSO handshake, short-lived access tokens with refresh token rotation.
- MFA enforced at the IdP level (inherited from organizational policy).
- All API requests require a valid, non-expired token; unauthenticated requests rejected with `401`.

## 4. Authorization (RBAC)

| Role | Permissions |
|---|---|
| **Executive/Viewer** | Read-only access to dashboard KPIs and aggregated segment views. No access to individual customer PII detail. |
| **Retention Manager** | Read access to customer list, customer detail (including risk score, recommendation), export at-risk lists. No access to model training/config. |
| **Data/ML Analyst** | Read access to model metrics, feature importance, drift reports. Can trigger scoring jobs. No access to raw PII fields beyond what's needed for feature validation. |
| **Admin** | Full access: user/role management, model promotion approval, retraining triggers, audit log access. |

- Enforcement occurs at the API layer (FastAPI dependency-injected permission checks) — never trust frontend-only role gating.
- Principle of least privilege: each role's endpoints and field-level data exposure are explicitly allow-listed, not default-open.

## 5. Field-Level Data Protection

- **Masking:** Direct PII fields (name, phone, address) are masked by default in list/table views (e.g., `+91-XXXXX-1234`) and only revealed in the single-customer detail view to roles authorized to see PII (Retention Manager, Admin).
- **Tokenization option:** Where feasible, replace direct identifiers with a stable internal token/customer ID for ML processing and analyst-facing views, decoupling model training from raw PII.
- **No PII in logs:** Application logs and error traces must never include raw PII fields — use the internal customer ID only.
- **No PII in model artifacts:** Ensure that direct identifiers are excluded from the feature set used for training/inference; only behavioral/usage features are used as model inputs.

## 6. Transport & Storage Security

- **In transit:** All frontend↔backend and backend↔database traffic over TLS 1.2+.
- **At rest:** PostgreSQL encryption at rest (managed DB encryption or disk-level encryption); Parquet files stored in encrypted object storage.
- **Model registry artifacts:** Access-controlled storage bucket/table; model files not publicly accessible.
- **Secrets management:** Database credentials, SSO client secrets, and API keys stored in a secrets manager (e.g., environment-injected via a vault), never hard-coded or committed to source control.

## 7. Audit Logging

- All access to individual customer PII detail views is logged (who, when, which customer record).
- All model promotion, retraining trigger, and configuration changes are logged with actor identity and timestamp.
- All export actions (CSV download of at-risk customer lists) are logged, since exports move data outside the controlled environment.
- Audit logs retained per organizational data retention policy and accessible only to Admin role.

## 8. Data Retention & Deletion

- Raw usage/call-log data retention period defined by organizational policy and applicable telecom data regulations (to be confirmed with Legal/Compliance — flagged as an open question in the PRD).
- Churned/closed customer records: retained per policy for historical model training but reviewed periodically for anonymization or deletion eligibility.
- Right-to-erasure requests (where applicable jurisdiction requires it) must be supported via an admin-triggered deletion workflow that removes/anonymizes the customer's PII while optionally preserving anonymized behavioral data for aggregate model training.

## 9. Compliance Considerations

- Treat customer usage and call-log data under applicable telecom/data-protection regulations relevant to the operating jurisdiction (e.g., India's DPDP Act, or GDPR/local equivalents if operating elsewhere) — legal review required before production rollout.
- Customer service call log content (if transcripts are included) may require additional consent/retention handling — confirm with Legal whether transcripts vs. call metadata/summary-only is used as model input.
- Model decisions influencing customer treatment (e.g., who gets a retention discount) should be explainable (SHAP) and subject to human review — avoid fully automated adverse actions without oversight.

## 10. Threat Model Summary

| Threat | Mitigation |
|---|---|
| Unauthorized access to customer PII | SSO + RBAC + field-level masking |
| Data exfiltration via export | Export logging, role-restricted export permission |
| Model/artifact theft | Access-controlled model registry, no public endpoint exposure |
| SQL injection / API abuse | Pydantic validation, parameterized queries (ORM), rate limiting |
| Insider misuse (analyst viewing PII unnecessarily) | Least-privilege roles, audit logging, periodic access review |
| Data drift causing biased/harmful recommendations | Drift monitoring, human review before acting on model recommendations |

## 11. Security Review Cadence

- Access review (who has which role) — quarterly.
- Dependency/vulnerability scanning (frontend and backend packages) — on each release + scheduled scans.
- Penetration test / security assessment — prior to production go-live, then annually.
