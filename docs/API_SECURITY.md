# API Security, Rate Limiting & Abuse Protection Architecture

This document describes the production security architecture, rate limiting policies, abuse protection mechanisms, and defense-in-depth controls implemented in the CCATI Telecom Customer Churn Platform.

---

## 1. Authentication & Session Management
- **Zero-Trust JWT**: Stateless JSON Web Tokens signed with HMAC-SHA256 (`HS256`).
- **Token Lifecycles**:
  - **Access Token**: Short-lived (default `60 minutes`), verified cryptographically on every request.
  - **Refresh Token**: Long-lived (default `7 days`), distinct cryptographic type (`"refresh"`), single-use rotation.
- **Server-Side Active Verification**: Token claims are validated against the authoritative user database on every request to immediately reject deactivated or locked accounts.

---

## 2. Role-Based Access Control (RBAC)
- **Authoritative Server Enforcement**: Permissions are determined server-side; client role claims are never blindly trusted.
- **Canonical Roles**:
  - `Admin`: Full platform administration, user management, audit logs, model promotion.
  - `RetentionManager`: Customer intelligence, risk triage, retention actions, unmasking PII, CSV exports.
  - `Analyst`: Model performance analysis, segmentation, churn predictions, metrics exploration.
  - `ModelManager`: ML registry governance, model promotion, drift monitoring.
  - `Operations`: Customer monitoring, operational health tracking.
  - `Viewer`: Read-only view of customer dashboards and analytics.
  - `Executive`: Strategic high-level overview metrics and macro insights.

---

## 3. Rate Limiting Architecture
- **Algorithm**: In-Memory Sliding Window Counter (`InMemorySlidingWindowStore`) with thread-safe lock management.
- **Distributed Interface**: Extensible `BaseRateLimitStore` base class supporting Redis cluster backends in multi-instance production environments.
- **Configurable Rate Limits**:
  | Category | Default Limit | Target Endpoints | Behavior on Breach |
  |---|---|---|---|
  | `auth` | 15 req/min | `/api/v1/auth/login`, `/api/v1/auth/refresh` | HTTP 429 + `Retry-After` |
  | `prediction` | 60 req/min | `/api/v1/predict`, `/api/v1/predict/{id}` | HTTP 429 + `Retry-After` |
  | `read` | 120 req/min | `/api/v1/customers`, `/api/v1/segments`, `/api/v1/analytics/*`, `/api/v1/metrics`, `/api/v1/audit/events` | HTTP 429 + `Retry-After` |
  | `admin` | 30 req/min | `/api/v1/admin/*`, `/api/v1/scoring-jobs`, `/api/v1/models/promote/*`, `/customers/{id}/action` | HTTP 429 + `Retry-After` |
  | `export` | 10 req/min | `/api/v1/export/customers` | HTTP 429 + `Retry-After` |
  | `health` | Unlimited | `/health`, `/ready`, `/` | Unrestricted |

### Rate Limit Response Schema (HTTP 429)
```json
{
  "detail": "Too many requests for 'auth' operations. Rate limit of 15 requests per minute exceeded.",
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests for 'auth' operations. Rate limit of 15 requests per minute exceeded.",
    "request_id": "req-ad5e5f39a4af"
  }
}
```
**Headers Returned**: `Retry-After: <seconds_until_window_slides>`

---

## 4. Brute-Force Protection & Account Lockout
- **Failed Attempt Tracking**: Consecutive failed authentication attempts increment `failed_login_attempts` on the user record.
- **Temporary Lockout**: Reaching `MAX_FAILED_LOGIN_ATTEMPTS` (default `5`) locks the user account for `ACCOUNT_LOCKOUT_MINUTES` (default `15`).
- **User Enumeration Prevention**: All login failures return generic error messages (`"Invalid email/username or password."`) regardless of whether the email or username exists in the system.

---

## 5. Input Validation & Pagination Protection
- **Pydantic Schema Validation**: All request bodies are strictly typed and validated before reaching route handlers.
- **Pagination Capping**:
  - `page`: Must be `ge=1`.
  - `page_size`: Must be `ge=1` and `le=MAX_PAGE_SIZE` (default `100`).
  - Requests exceeding `MAX_PAGE_SIZE` or negative page numbers are rejected with `HTTP 422 Unprocessable Entity`.
- **Sorting Allowlist**: Sort fields are validated against strict regex patterns (e.g. `^(priority_score|churn_probability|tenure_months|monthly_charges)$`).

---

## 6. HTTP Security Headers
Applied globally via `security_and_observability_middleware`:
- `X-Content-Type-Options: nosniff`: Prevents MIME-type sniffing.
- `X-Frame-Options: DENY`: Blocks clickjacking attacks by forbidding iframe embedding.
- `X-XSS-Protection: 1; mode=block`: Enables browser XSS filtering.
- `Referrer-Policy: strict-origin-when-cross-origin`: Controls referrer leakage.
- `Permissions-Policy: geolocation=(), camera=(), microphone=(), payment=()`: Restricts sensitive browser APIs.
- `Content-Security-Policy: default-src 'self'; frame-ancestors 'none';`: Restricts origin loading and embedding.
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`: Enforces HTTPS in production (`ENABLE_HSTS=true`).
- `Cache-Control: no-store, no-cache, must-revalidate, max-age=0`: Prevents intermediate caching of sensitive API data.

---

## 7. CORS Hardening
- **Explicit Allowed Origins**: Governed strictly by `ALLOWED_ORIGINS` in `.env` (e.g. `http://localhost:5173,https://app.telecom.com`).
- **No Wildcards with Credentials**: Wildcard origins `*` are forbidden when `allow_credentials=True`.
- **Exposed Headers**: Only safe correlation headers are exposed to frontend clients (`X-Correlation-ID`, `X-Request-ID`, `X-Process-Time-MS`).

---

## 8. Payload Size Protection
- Requests exceeding `MAX_REQUEST_SIZE_BYTES` (default `10 MB`) are rejected immediately in middleware with `HTTP 413 Payload Too Large`.

---

## 9. Path Traversal & Injection Protection
- **Route Parameters**: Parameters like `/models/promote/{version}` are validated against regex `^[a-zA-Z0-9_.-]+$` to reject `..`, `/`, `\\`.
- **SQL Injection Defense**: 100% of SQLite and PostgreSQL queries use parameterized bindings (`?` or `%s`) or ORM abstractions. Zero string concatenation in SQL statements.

---

## 10. Trusted Proxy & Client IP Handling
- Client IP resolution safely inspects `X-Forwarded-For` **only** if the immediate connection originates from an IP listed in `TRUSTED_PROXIES` (e.g. `127.0.0.1`, Nginx / Cloudflare ingress proxies).
- Prevents IP spoofing attacks intended to bypass rate limits.

---

## 11. Request Correlation & Observability
- **Header Propagation**: Every request receives a unique `X-Request-ID` (and `X-Correlation-ID`), either generated (`req-<uuid>`) or validated from incoming client headers.
- **Traceability**: All log entries, audit events, and error payloads embed the request ID for cross-system correlation.

---

## 12. Safe Error Handling & Information Leakage Prevention
- **Centralized Exception Handlers**:
  - `StarletteHTTPException`: Standardized code and message.
  - `RequestValidationError`: Clean list of field errors with code `VALIDATION_ERROR`.
  - `Exception`: Unhandled 500 exceptions log tracebacks internally and return a generic error message with the request ID.
  - Zero SQL errors, filesystem paths, or stack traces are ever returned to clients.
