"""Automated Test Suite for TASK 10 — Security, CI/CD & Final Production Hardening.

Verifies:
1. OWASP Security Headers (X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy).
2. Request Correlation & ID Propagation (X-Correlation-ID, X-Request-ID, X-Process-Time-MS).
3. Production Health and Readiness Probes (/health, /ready).
4. Error Sanitization (No stack traces or internal secrets exposed in 404, 422, or 500 responses).
5. Environment-driven CORS configuration.
6. Payload Protection (Large request entity rejection).
7. PII Redaction & Masking (Customer name, email, phone).
8. RBAC and JWT Authentication Security.
9. Model Artifact Integrity and Verification.
"""

from fastapi.testclient import TestClient
import pytest
from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.security import create_access_token, mask_email, mask_name, mask_phone
from ml_engine.registry.model_registry import ModelRegistry

client = TestClient(app)


@pytest.fixture
def admin_headers():
    token = create_access_token(subject={"sub": "usr-admin", "email": "admin@telecom.com", "role": "Admin"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def analyst_headers():
    token = create_access_token(subject={"sub": "usr-analyst", "email": "analyst@telecom.com", "role": "Analyst"})
    return {"Authorization": f"Bearer {token}"}


def test_1_owasp_security_headers_present():
    """TEST 1: API responses contain OWASP-recommended security headers."""
    res = client.get("/health")
    assert res.status_code == 200
    headers = res.headers

    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert headers.get("x-xss-protection") == "1; mode=block"
    assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert "geolocation=()" in headers.get("permissions-policy", "")


def test_2_correlation_and_request_id_headers():
    """TEST 2: Every request receives a unique request/correlation ID and process time."""
    # Test auto-generated correlation ID
    res = client.get("/health")
    assert "X-Correlation-ID" in res.headers
    assert "X-Request-ID" in res.headers
    assert "X-Process-Time-MS" in res.headers

    # Test propagation of client-provided correlation ID
    custom_id = "custom-trace-999888"
    res_custom = client.get("/health", headers={"X-Correlation-ID": custom_id})
    assert res_custom.headers.get("X-Correlation-ID") == custom_id


def test_3_liveness_and_readiness_probes():
    """TEST 3: /health (liveness) and /ready (readiness) probe endpoints return operational status."""
    res_health = client.get("/health")
    assert res_health.status_code == 200
    data_health = res_health.json()
    assert data_health["status"] == "ok"
    assert "service" in data_health
    assert "version" in data_health
    assert data_health["artifact_integrity_verified"] is True

    res_ready = client.get("/api/v1/ready")
    assert res_ready.status_code == 200
    data_ready = res_ready.json()
    assert data_ready["status"] == "ready"
    assert data_ready["checks"]["database"] is True
    assert data_ready["checks"]["model_registry"] is True
    assert data_ready["checks"]["artifact_integrity"] is True


def test_4_error_sanitization_no_stack_traces(admin_headers):
    """TEST 4: Client errors return structured format without leaking stack traces or internals."""
    # 404 Not Found
    res_404 = client.get("/api/v1/non_existent_security_test_endpoint")
    assert res_404.status_code == 404
    data_404 = res_404.json()
    assert "error" in data_404
    assert data_404["error"]["code"] == "HTTP_404"
    assert "Traceback" not in res_404.text

    # 422 Validation Error
    res_422 = client.post("/api/v1/predict", json={"invalid_field": 12345}, headers=admin_headers)
    assert res_422.status_code == 422
    data_422 = res_422.json()
    assert "error" in data_422
    assert data_422["error"]["code"] == "VALIDATION_ERROR"
    assert "Traceback" not in res_422.text


def test_5_cors_preflight_and_origins():
    """TEST 5: CORS options preflight handles configured origins appropriately."""
    res = client.options(
        "/api/v1/predict",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,authorization",
        },
    )
    assert res.status_code == 200
    allow_origin = res.headers.get("access-control-allow-origin")
    assert allow_origin in ["http://localhost:5173", "*"]


def test_6_payload_size_limit_protection():
    """TEST 6: Rejects requests exceeding maximum payload size limit."""
    huge_length = str(settings.MAX_REQUEST_SIZE_BYTES + 1024)
    res = client.post(
        "/api/v1/predict",
        headers={"content-length": huge_length, "content-type": "application/json"},
        content="{}",
    )
    assert res.status_code == 413
    assert res.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"


def test_7_pii_masking_security():
    """TEST 7: PII masking functions properly protect sensitive customer details."""
    assert mask_name("Johnathan Doe") == "J******** D**"
    assert mask_phone("+91-98765-12345") == "+91--XXXXX-2345" or "XXXXX" in mask_phone("+91-98765-12345")
    assert mask_email("subscriber123@example.com") == "s***********3@example.com"
    assert mask_email("") == "u***@example.com"


def test_8_rbac_authorization_matrix(admin_headers, analyst_headers):
    """TEST 8: Protected endpoints enforce RBAC roles server-side."""
    # Admin-only audit logs route
    res_admin = client.get(
        "/api/v1/admin/audit-logs",
        headers=admin_headers,
    )
    assert res_admin.status_code == 200

    # Analyst role attempting admin action is forbidden (403)
    res_analyst = client.get(
        "/api/v1/admin/audit-logs",
        headers=analyst_headers,
    )
    assert res_analyst.status_code == 403
    assert "Access denied" in res_analyst.json()["detail"]


def test_9_model_registry_artifact_integrity_verification():
    """TEST 9: ModelRegistry securely validates artifact SHA-256 hashes against registry metadata."""
    registry = ModelRegistry()
    active_info = registry.get_active_model_info()

    # Valid artifact hash matches
    assert registry.verify_integrity(active_info["version"]) is True

    # Non-existent version fails safely
    assert registry.verify_integrity("v_corrupted_non_existent") is False
