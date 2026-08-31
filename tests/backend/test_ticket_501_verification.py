"""Verification test suite for TICKET-501 (FastAPI Scaffold, Schemas & OpenAPI docs)."""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_check_endpoint():
    """Verify GET /health returns status ok and API version."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_openapi_docs_rendering():
    """Verify GET /docs renders Swagger UI HTML cleanly."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Swagger UI" in response.text or "swagger-ui" in response.text.lower()


def test_openapi_schema_completeness():
    """Verify GET /openapi.json registers all required routes and schemas."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()

    paths = schema.get("paths", {})
    assert "/health" in paths
    assert "/api/v1/customers" in paths
    assert "/api/v1/customers/{customer_id}" in paths
    assert "/api/v1/segments" in paths
    assert "/api/v1/segments/{segment_id}" in paths
    assert "/api/v1/models/metrics" in paths
    assert "/api/v1/scoring-jobs" in paths
    assert "/api/v1/export/customers" in paths
    assert "/api/v1/auth/login" in paths

    components = schema.get("components", {}).get("schemas", {})
    assert "CustomerListItem" in components
    assert "CustomerDetailResponse" in components
    assert "SegmentProfile" in components
    assert "ModelMetricsResponse" in components
    assert "ScoringJobResponse" in components
