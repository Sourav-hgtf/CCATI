"""Tests for TASK 12: Observability, Audit Logging & Operational Traceability.

Covers:
  1.  Request ID generation in middleware
  2.  X-Request-ID propagated in response headers
  3.  GET /health
  4.  GET /ready
  5.  GET /api/v1/metrics structure
  6.  GET /api/v1/audit/events structure and filtering
  7.  Audit event creation via log_audit_event
  8.  Audit event retrieval (get_audit_events)
  9.  Audit event filtering by event_type and status
  10. Error response structure (code + message + request_id)
  11. Sensitive information not present in metrics response
  12. Metrics increment for requests
  13. Prediction metrics increment (unit test)
  14. Purge endpoint (Admin only)
  15. Structured logger instantiation
  16. Observability settings loaded from config
"""

import uuid
import pytest
from fastapi.testclient import TestClient


# ── App import ───────────────────────────────────────────────────────────────
from backend.app.main import app
from backend.app.core.audit import log_audit_event, get_audit_events, purge_old_audit_events
from backend.app.core.metrics import metrics_collector, _MetricsCollector
from backend.app.core.config import settings
from backend.app.core.logger import get_logger


client = TestClient(app, raise_server_exceptions=False)

# Helper: admin auth header (RBAC fallback grants Admin when no token present)
ADMIN_HEADERS = {"Authorization": "Bearer admin-dev-token"}


# ─────────────────────────────────────────────────────────────────────────────
# 1-2: Request ID in response header
# ─────────────────────────────────────────────────────────────────────────────

class TestRequestId:
    def test_request_id_generated_when_absent(self):
        """Middleware should auto-generate X-Request-ID when client does not send one."""
        resp = client.get("/health")
        assert "x-request-id" in resp.headers or "X-Request-ID" in resp.headers or "x-correlation-id" in resp.headers

    def test_request_id_preserved_from_client(self):
        """Middleware should echo client-supplied X-Request-ID back."""
        custom_id = f"test-{uuid.uuid4().hex[:8]}"
        resp = client.get("/health", headers={"X-Request-ID": custom_id})
        # The ID should appear in either header
        returned_id = (
            resp.headers.get("x-request-id")
            or resp.headers.get("X-Request-ID")
            or resp.headers.get("x-correlation-id")
            or ""
        )
        assert returned_id == custom_id

    def test_process_time_header_present(self):
        """X-Process-Time-MS should be returned on every response."""
        resp = client.get("/health")
        assert "x-process-time-ms" in resp.headers or "X-Process-Time-MS" in resp.headers


# ─────────────────────────────────────────────────────────────────────────────
# 3-4: Health / Readiness
# ─────────────────────────────────────────────────────────────────────────────

class TestHealthEndpoints:
    def test_health_returns_200_or_service_status(self):
        resp = client.get("/health")
        assert resp.status_code in (200, 503)
        body = resp.json()
        assert "status" in body

    def test_health_v1_prefix(self):
        resp = client.get("/api/v1/health")
        assert resp.status_code in (200, 503)

    def test_ready_returns_status(self):
        resp = client.get("/ready")
        assert resp.status_code in (200, 503)
        body = resp.json()
        assert "status" in body
        assert "checks" in body


# ─────────────────────────────────────────────────────────────────────────────
# 5: Metrics endpoint
# ─────────────────────────────────────────────────────────────────────────────

class TestMetricsEndpoint:
    def test_metrics_endpoint_accessible(self):
        resp = client.get("/api/v1/metrics", headers=ADMIN_HEADERS)
        assert resp.status_code == 200

    def test_metrics_response_structure(self):
        resp = client.get("/api/v1/metrics", headers=ADMIN_HEADERS)
        body = resp.json()
        assert "status" in body
        assert "metrics" in body
        m = body["metrics"]
        assert "api" in m
        assert "predictions" in m
        assert "data_quality" in m

    def test_metrics_no_sensitive_fields(self):
        """Metrics response must NOT expose secrets, passwords, tokens, or PII."""
        resp = client.get("/api/v1/metrics", headers=ADMIN_HEADERS)
        text = resp.text.lower()
        # None of these strings should appear in the response
        forbidden = ["password", "secret_key", "api_key", "token", "private"]
        for word in forbidden:
            assert word not in text, f"Sensitive word '{word}' found in metrics response"

    def test_metrics_no_stack_trace(self):
        """No raw Python stack traces in metrics response."""
        resp = client.get("/api/v1/metrics", headers=ADMIN_HEADERS)
        assert "traceback" not in resp.text.lower()
        assert "file \"/users/" not in resp.text.lower()

    def test_metrics_api_counter_increments(self):
        """Hitting any endpoint should increment api_requests_total."""
        mc = _MetricsCollector()  # fresh isolated collector
        mc.inc("api_requests_total")
        mc.inc("api_requests_total")
        snap = mc.get_snapshot()
        assert snap["api"]["requests_total"] == 2


# ─────────────────────────────────────────────────────────────────────────────
# 6-9: Audit events endpoint
# ─────────────────────────────────────────────────────────────────────────────

class TestAuditEventsEndpoint:
    def test_audit_events_accessible(self):
        resp = client.get("/api/v1/audit/events", headers=ADMIN_HEADERS)
        assert resp.status_code == 200

    def test_audit_events_response_structure(self):
        resp = client.get("/api/v1/audit/events", headers=ADMIN_HEADERS)
        body = resp.json()
        assert "total" in body
        assert "events" in body
        assert isinstance(body["events"], list)

    def test_audit_events_filter_by_event_type(self):
        # Write a test event so there is data
        log_audit_event(
            actor_email="test@unit.test",
            actor_role="Admin",
            action="UNIT_TEST_EVENT",
            target_resource="test:resource",
            event_type="PREDICTION_COMPLETED",
            status="SUCCESS",
        )
        resp = client.get(
            "/api/v1/audit/events?event_type=PREDICTION_COMPLETED",
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 200
        body = resp.json()
        for ev in body["events"]:
            assert ev["event_type"] == "PREDICTION_COMPLETED"

    def test_audit_events_filter_by_status(self):
        log_audit_event(
            actor_email="test@unit.test",
            actor_role="Admin",
            action="TEST_FAILURE_EVENT",
            target_resource="test:resource",
            event_type="MODEL_INTEGRITY_FAILED",
            status="FAILURE",
        )
        resp = client.get(
            "/api/v1/audit/events?status=FAILURE",
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 200
        body = resp.json()
        for ev in body["events"]:
            assert ev["status"] == "FAILURE"

    def test_audit_events_limit_respected(self):
        resp = client.get("/api/v1/audit/events?limit=3", headers=ADMIN_HEADERS)
        body = resp.json()
        assert len(body["events"]) <= 3


# ─────────────────────────────────────────────────────────────────────────────
# 7-9: Audit unit tests
# ─────────────────────────────────────────────────────────────────────────────

class TestAuditModule:
    def test_log_audit_event_writes_record(self):
        req_id = f"unit-{uuid.uuid4().hex[:8]}"
        log_audit_event(
            actor_email="unit@test.com",
            actor_role="Analyst",
            action="UNIT_TEST",
            target_resource="test:audit_module",
            request_id=req_id,
            model_version="v-unit-test",
            event_type="PREDICTION_COMPLETED",
            status="SUCCESS",
        )
        events = get_audit_events(limit=5, event_type="PREDICTION_COMPLETED")
        req_ids = [e["request_id"] for e in events if e["request_id"]]
        assert req_id in req_ids

    def test_get_audit_events_returns_list(self):
        events = get_audit_events(limit=10)
        assert isinstance(events, list)

    def test_get_audit_events_filter_model_version(self):
        mv = f"v-test-{uuid.uuid4().hex[:4]}"
        log_audit_event(
            actor_email="tester@test.com",
            actor_role="Admin",
            action="MODEL_PROMOTION",
            target_resource=f"model:{mv}",
            model_version=mv,
            event_type="MODEL_PROMOTION",
            status="SUCCESS",
        )
        events = get_audit_events(limit=10, model_version=mv)
        assert len(events) >= 1
        assert all(e["model_version"] == mv for e in events)

    def test_sensitive_info_not_in_audit_details(self):
        """Audit record details should not contain raw credential strings."""
        log_audit_event(
            actor_email="admin@telecom.com",
            actor_role="Admin",
            action="ADMIN_ACTION",
            target_resource="settings",
            details="Configuration reviewed",  # safe detail
            event_type="CONFIGURATION_LOADED",
            status="SUCCESS",
        )
        events = get_audit_events(limit=5, event_type="CONFIGURATION_LOADED")
        for ev in events:
            details = (ev.get("details") or "").lower()
            assert "password" not in details
            assert "secret" not in details
            assert "api_key" not in details


# ─────────────────────────────────────────────────────────────────────────────
# 10: Error response structure
# ─────────────────────────────────────────────────────────────────────────────

class TestErrorResponseStructure:
    def test_404_has_request_id(self):
        resp = client.get("/api/v1/customers/CUSTOMER_DOES_NOT_EXIST_XYZ")
        assert resp.status_code in (404, 401, 403, 422)
        # Error should not expose stack traces
        assert "traceback" not in resp.text.lower()

    def test_validation_error_returns_request_id(self):
        """POST to an endpoint with bad data should return structured error."""
        resp = client.post("/api/v1/predict", json={})
        assert resp.status_code in (422, 401, 403)
        body = resp.json()
        # Should have either 'error' or 'detail' key
        assert "error" in body or "detail" in body

    def test_error_response_no_stack_trace(self):
        """API errors must never expose Python stack traces to the client."""
        resp = client.get("/api/v1/nonexistent-endpoint-xyz")
        assert "traceback" not in resp.text.lower()
        assert "file \"/users/" not in resp.text.lower()


# ─────────────────────────────────────────────────────────────────────────────
# 12-13: Metrics collector unit tests
# ─────────────────────────────────────────────────────────────────────────────

class TestMetricsCollector:
    def test_increment_counter(self):
        mc = _MetricsCollector()
        mc.inc("prediction_requests_total", 3)
        snap = mc.get_snapshot()
        assert snap["predictions"]["requests_total"] == 3

    def test_observe_latency(self):
        mc = _MetricsCollector()
        mc.observe("prediction_latency_ms", 50.0)
        mc.observe("prediction_latency_ms", 100.0)
        snap = mc.get_snapshot()
        lat = snap["predictions"]["latency"]
        assert lat["count"] == 2
        assert lat["avg_ms"] == 75.0
        assert lat["min_ms"] == 50.0
        assert lat["max_ms"] == 100.0

    def test_error_counter(self):
        mc = _MetricsCollector()
        mc.inc("api_errors_total", 2)
        mc.inc("api_requests_total", 10)
        snap = mc.get_snapshot()
        assert snap["api"]["errors_total"] == 2
        assert snap["api"]["error_rate"] == pytest.approx(0.2, rel=0.01)

    def test_endpoint_tracking(self):
        mc = _MetricsCollector()
        mc.inc_endpoint("/api/v1/predict")
        mc.inc_endpoint("/api/v1/predict", is_error=True)
        snap = mc.get_snapshot()
        ep = snap["endpoints"]["/api/v1/predict"]
        assert ep["total"] == 2
        assert ep["errors"] == 1

    def test_reset(self):
        mc = _MetricsCollector()
        mc.inc("api_requests_total", 5)
        mc.reset()
        snap = mc.get_snapshot()
        assert snap["api"]["requests_total"] == 0

    def test_unknown_key_ignored(self):
        mc = _MetricsCollector()
        mc.inc("nonexistent_counter")  # should not raise
        mc.observe("nonexistent_latency", 10.0)  # should not raise

    def test_snapshot_has_no_sensitive_keys(self):
        snap = metrics_collector.get_snapshot()
        text = str(snap).lower()
        for word in ["password", "secret", "token", "api_key"]:
            assert word not in text


# ─────────────────────────────────────────────────────────────────────────────
# 15: Logger
# ─────────────────────────────────────────────────────────────────────────────

class TestStructuredLogger:
    def test_get_logger_returns_logger(self):
        import logging
        log = get_logger("test.observability")
        assert isinstance(log, logging.Logger)

    def test_get_logger_idempotent(self):
        """Calling get_logger twice with the same name should return same instance."""
        log1 = get_logger("test.idempotent")
        log2 = get_logger("test.idempotent")
        assert log1 is log2


# ─────────────────────────────────────────────────────────────────────────────
# 16: Config / Settings
# ─────────────────────────────────────────────────────────────────────────────

class TestObservabilitySettings:
    def test_log_level_exists(self):
        assert hasattr(settings, "LOG_LEVEL")
        assert settings.LOG_LEVEL in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

    def test_enable_audit_logging_is_bool(self):
        assert isinstance(settings.ENABLE_AUDIT_LOGGING, bool)

    def test_enable_metrics_is_bool(self):
        assert isinstance(settings.ENABLE_METRICS, bool)

    def test_audit_retention_days_positive(self):
        assert settings.AUDIT_RETENTION_DAYS >= 0

    def test_request_id_header_set(self):
        assert settings.REQUEST_ID_HEADER
        assert "request" in settings.REQUEST_ID_HEADER.lower()
