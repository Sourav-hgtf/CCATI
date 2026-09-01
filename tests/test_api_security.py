"""Comprehensive Automated Test Suite for TASK 19: Production API Security, Rate Limiting & Abuse Protection.

Covers:
  1.  Input validation & Malformed request rejection (422)
  2.  Pagination protection (MAX_PAGE_SIZE enforcement)
  3.  Rate limiting enforcement (HTTP 429 & Retry-After header)
  4.  Rate limit response payload structure
  5.  Login brute-force protection & Account lockout
  6.  User enumeration prevention (generic auth errors)
  7.  CORS configuration and credentials safety
  8.  HTTP Security Headers (OWASP: nosniff, DENY, CSP, Cache-Control, HSTS)
  9.  Request payload size protection (HTTP 413)
  10. Path traversal protection on parameters
  11. SQL injection rejection with parameterized queries
  12. Unauthorized API access rejection (401/403)
  13. Request ID auto-generation and client propagation
  14. Error sanitization (no stack traces or internal secrets in responses)
  15. Health endpoints safety (no infrastructure credentials leaked)
  16. Role-based resource isolation (Customer PII access control)
"""

import time
import uuid
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.rate_limiter import (
    InMemorySlidingWindowStore,
    RateLimiter,
    _default_store,
)
from backend.app.core.security import create_access_token
from backend.app.db.base import Base
from backend.app.db.session import engine
from backend.scripts.seed_users import seed_database_users

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    seed_database_users()


@pytest.fixture(autouse=True)
def reset_rate_limiters():
    """Reset rate limiter counters before each test."""
    _default_store.reset()
    yield
    _default_store.reset()


def get_token(role: str = "Admin") -> str:
    role_email_map = {
        "Admin": ("admin@telecom.com", "AdminPassword123!"),
        "RetentionManager": ("manager@telecom.com", "ManagerPassword123!"),
        "Analyst": ("analyst@telecom.com", "AnalystPassword123!"),
        "ModelManager": ("modelmanager@telecom.com", "ModelPassword123!"),
        "Operations": ("operations@telecom.com", "OpsPassword123!"),
        "Viewer": ("viewer@telecom.com", "ViewerPassword123!"),
    }
    email, password = role_email_map.get(role, ("admin@telecom.com", "AdminPassword123!"))
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


# ── 1. Request Validation & Malformed Input ──────────────────────────────────

def test_1_invalid_payload_rejected_with_422():
    """Malformed request payload with missing required fields returns 422 with validation error code."""
    res = client.post("/api/v1/auth/login", json={})
    assert res.status_code == 422
    data = res.json()
    assert "detail" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "request_id" in data["error"]


def test_2_invalid_field_types_rejected():
    """Sending invalid types (e.g. string for boolean, invalid numbers) is rejected cleanly."""
    token = get_token("Admin")
    res = client.post(
        "/api/v1/scoring-jobs",
        json={"job_type": "BATCH_SCORING", "force_ingestion": "not-a-bool"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


# ── 2. Pagination Protection ─────────────────────────────────────────────────

def test_3_pagination_limits_capped():
    """Pagination query params respect upper bound (ge=1, le=100)."""
    token = get_token("Analyst")
    # Page size > 100 should be rejected with 422
    res = client.get(
        "/api/v1/customers?page=1&page_size=999999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 422

    # Negative page number should be rejected
    res_neg = client.get(
        "/api/v1/customers?page=-1&page_size=10",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_neg.status_code == 422


# ── 3. Rate Limiting & 429 Too Many Requests ─────────────────────────────────

def test_4_rate_limiting_enforced_and_returns_429():
    """Exceeding category rate limit triggers HTTP 429 with standard error structure & Retry-After."""
    from backend.app.core.rate_limiter import rate_limit_auth
    custom_store = InMemorySlidingWindowStore()
    limiter = RateLimiter(category="auth", limit_override=3, window_seconds=60, store=custom_store)

    app.dependency_overrides[rate_limit_auth] = limiter
    try:
        # 3 allowed requests
        for _ in range(3):
            res = client.post(
                "/api/v1/auth/login",
                json={"email": "nonexistent@telecom.com", "password": "WrongPassword123!"},
            )
            assert res.status_code in (401, 200)

        # 4th request must be blocked with 429
        blocked_res = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@telecom.com", "password": "WrongPassword123!"},
        )
        assert blocked_res.status_code == 429
        body = blocked_res.json()
        assert body["error"]["code"] == "RATE_LIMIT_EXCEEDED"
        assert "Retry-After" in blocked_res.headers
        assert int(blocked_res.headers["Retry-After"]) >= 1
    finally:
        app.dependency_overrides.pop(rate_limit_auth, None)


def test_5_rate_limit_sliding_window_resets():

    """Sliding window allows new requests after expiration."""
    store = InMemorySlidingWindowStore()
    # 2 requests per 1 second window
    allowed1, _, _ = store.is_allowed("test:client", limit=2, window_seconds=1)
    allowed2, _, _ = store.is_allowed("test:client", limit=2, window_seconds=1)
    allowed3, _, retry_after = store.is_allowed("test:client", limit=2, window_seconds=1)

    assert allowed1 is True
    assert allowed2 is True
    assert allowed3 is False
    assert retry_after >= 1

    # Wait for window to expire
    time.sleep(1.1)
    allowed4, _, _ = store.is_allowed("test:client", limit=2, window_seconds=1)
    assert allowed4 is True


# ── 4. Brute-Force Protection & User Enumeration ─────────────────────────────

def test_6_user_enumeration_prevention():
    """Authentication failures return generic error whether email exists or not."""
    # Non-existent user
    res1 = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody_exists_123@telecom.com", "password": "Password123!"},
    )
    assert res1.status_code == 401
    assert "Invalid email/username or password" in res1.json()["detail"]

    # Existing user with wrong password
    res2 = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@telecom.com", "password": "WrongPassword999!"},
    )
    assert res2.status_code == 401
    assert "Invalid email/username or password" in res2.json()["detail"]


def test_7_account_lockout_after_max_failed_attempts():
    """Account is temporarily locked after reaching MAX_FAILED_LOGIN_ATTEMPTS."""
    # Seed or reset admin attempts
    for _ in range(settings.MAX_FAILED_LOGIN_ATTEMPTS):
        client.post(
            "/api/v1/auth/login",
            json={"email": "viewer@telecom.com", "password": "WrongPassword!"},
        )

    # Next attempt should be rejected with 403 Account Locked
    locked_res = client.post(
        "/api/v1/auth/login",
        json={"email": "viewer@telecom.com", "password": "ViewerPassword123!"},
    )
    assert locked_res.status_code in (403, 401)


# ── 5. CORS Hardening ────────────────────────────────────────────────────────

def test_8_cors_headers_restrict_untrusted_origins():
    """CORS middleware does not allow unconfigured origins with credentials."""
    res = client.options(
        "/api/v1/customers",
        headers={
            "Origin": "http://evil-attacker-site.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    # Evil origin should not be reflected in Access-Control-Allow-Origin
    allow_origin = res.headers.get("access-control-allow-origin")
    assert allow_origin != "http://evil-attacker-site.com"
    assert allow_origin != "*"


def test_9_cors_allows_configured_origins():
    """Configured origins are properly allowed."""
    res = client.options(
        "/api/v1/customers",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert res.headers.get("access-control-allow-origin") == "http://localhost:5173"


# ── 6. HTTP Security Headers ─────────────────────────────────────────────────

def test_10_owasp_security_headers_present():
    """All OWASP recommended security headers are present on responses."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200

    headers = res.headers
    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert headers.get("x-xss-protection") == "1; mode=block"
    assert "strict-origin-when-cross-origin" in headers.get("referrer-policy", "")
    assert "camera=()" in headers.get("permissions-policy", "")
    assert "default-src 'self'" in headers.get("content-security-policy", "")


def test_11_cache_control_headers_on_api_routes():
    """API routes return Cache-Control: no-store to prevent browser caching of sensitive data."""
    token = get_token("Analyst")
    res = client.get("/api/v1/customers", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert "no-store" in res.headers.get("cache-control", "")
    assert res.headers.get("pragma") == "no-cache"


# ── 7. Request Payload Size Protection ───────────────────────────────────────

def test_12_payload_too_large_returns_413():
    """Payloads exceeding MAX_REQUEST_SIZE_BYTES are rejected with 413."""
    res = client.post(
        "/api/v1/auth/login",
        headers={"Content-Length": str(settings.MAX_REQUEST_SIZE_BYTES + 1024)},
        content=b"x" * 100,
    )
    assert res.status_code == 413
    assert res.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"


# ── 8. Path Traversal & Parameter Injection ──────────────────────────────────

def test_13_path_traversal_on_model_promote_rejected():
    """Path traversal attempts with ../ in route parameters are rejected."""
    token = get_token("Admin")
    res = client.post(
        "/api/v1/models/promote/..%2F..%2Fetc%2Fpasswd",
        headers={"Authorization": f"Bearer {token}"},
    )
    # FastAPI router / validation rejects traversal with 400 or 404 or 422
    assert res.status_code in (400, 404, 422)


def test_14_sql_injection_attempt_safely_handled():
    """SQL injection characters in query params are treated as literal strings and return 0 results."""
    token = get_token("Analyst")
    sqli_payload = "' OR '1'='1' --"
    res = client.get(
        f"/api/v1/customers?search={sqli_payload}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    # Parameterized query treats it as literal string — no SQL error, 0 matching records
    assert res.json()["total"] == 0


# ── 9. Request ID & Correlation Tracking ─────────────────────────────────────

def test_15_request_id_generated_and_propagated():
    """X-Request-ID is generated when absent and preserved when provided by client."""
    # Auto-generation
    res1 = client.get("/api/v1/health")
    assert "x-request-id" in res1.headers
    assert res1.headers["x-request-id"].startswith("req-")

    # Client-supplied ID
    custom_id = f"client-req-{uuid.uuid4().hex[:8]}"
    res2 = client.get("/api/v1/health", headers={"X-Request-ID": custom_id})
    assert res2.headers.get("x-request-id") == custom_id


# ── 10. Error Response Sanitization ──────────────────────────────────────────

def test_16_error_responses_contain_no_internal_stack_traces():
    """Error responses adhere to standard JSON error schema without leaking internals."""
    res = client.get("/api/v1/customers/NONEXISTENT-CUST-99999", headers={"Authorization": f"Bearer {get_token('Analyst')}"})
    assert res.status_code == 404
    data = res.json()
    assert "error" in data
    assert "code" in data["error"]
    assert "message" in data["error"]
    assert "request_id" in data["error"]
    assert "traceback" not in data
    assert "sqlite" not in str(data).lower()
    assert "/Users/" not in str(data)


# ── 11. Health Endpoint Hardening ────────────────────────────────────────────

def test_17_health_endpoints_do_not_leak_credentials():
    """Health endpoints expose only operational status, not DB passwords or paths."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "database_url" not in data
    assert "password" not in data
    assert "secret" not in data
    assert "DB_PATH" not in data


# ── 12. Resource Isolation & PII Protection ──────────────────────────────────

def test_18_unauthorized_user_cannot_reveal_pii():
    """Non-privileged roles cannot reveal unmasked customer PII."""
    analyst_token = get_token("Analyst")
    res = client.get(
        "/api/v1/customers/CUST-10001?reveal_pii=true",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"
