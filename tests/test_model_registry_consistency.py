"""Automated Test Suite for TASK 3 — Model Registry & Metadata Consistency.

Verifies that:
1. The Model Registry is the single source of truth for active production model metadata.
2. No hardcoded model names or version strings exist in production API endpoints.
3. Prediction responses (/predict) dynamically derive model metadata from ModelRegistry.
4. /model-info and /health accurately reflect active model metadata and SHA-256 integrity.
"""

from pathlib import Path
from fastapi.testclient import TestClient
import pytest
from backend.app.main import app
from backend.app.core.security import create_access_token
from ml_engine.registry.model_registry import ModelRegistry

client = TestClient(app)


@pytest.fixture
def auth_headers():
    token = create_access_token(subject={"sub": "test_user", "email": "test@telecom.com", "role": "Admin"})
    return {"Authorization": f"Bearer {token}"}


def test_1_active_model_registry_single_source_of_truth():
    """TEST 1: ModelRegistry returns exactly one active production model."""
    registry = ModelRegistry()
    active_info = registry.get_active_model_info()

    assert "model_name" in active_info
    assert "version" in active_info
    assert active_info["status"] == "PROMOTED"
    assert Path(active_info["artifact_path"]).exists()


def test_2_scoring_service_loads_active_model():
    """TEST 2: ModelRegistry loads the model defined in registry metadata."""
    registry = ModelRegistry()
    model, m_info = registry.get_model()

    assert model is not None
    assert m_info["status"] == "PROMOTED"


def test_3_model_info_api_matches_registry(auth_headers):
    """TEST 3: GET /model-info returns metadata matching ModelRegistry."""
    registry = ModelRegistry()
    active_info = registry.get_active_model_info()

    res = client.get("/api/v1/model-info", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["model_name"] == active_info["model_name"]
    assert data["model_version"] == active_info["version"]
    assert data["integrity_verified"] is True


def test_4_predict_response_contains_dynamic_registry_metadata(auth_headers):
    """TEST 4: /predict response includes dynamic model_name & model_version from registry."""
    registry = ModelRegistry()
    active_info = registry.get_active_model_info()

    res = client.post("/api/v1/predict", json={"customer_id": "CUST-10164"}, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["model_name"] == active_info["model_name"]
    assert data["model_version"] == active_info["version"]


def test_5_frontend_model_info_contract(auth_headers):
    """TEST 5: /model-info returns all required metadata fields for frontend display."""
    res = client.get("/api/v1/model-info", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    required_keys = ["status", "model_name", "model_version", "registered_at", "metrics", "sha256", "integrity_verified", "threshold"]
    for k in required_keys:
        assert k in data, f"Missing required model info key: {k}"


def test_6_no_hardcoded_model_version_in_predict(auth_headers):
    """TEST 6: /predict returns version from registry, matching /model-info."""
    res_info = client.get("/api/v1/model-info", headers=auth_headers).json()
    res_pred = client.post("/api/v1/predict", json={"customer_id": "CUST-10164"}, headers=auth_headers).json()

    assert res_info["model_version"] == res_pred["model_version"]
    assert res_info["model_name"] == res_pred["model_name"]


def test_7_sha256_artifact_integrity():
    """TEST 7: SHA-256 artifact checksum verification succeeds for active model."""
    registry = ModelRegistry()
    integrity_ok = registry.verify_integrity()
    assert integrity_ok is True


def test_8_health_endpoint_reflects_model_availability():
    """TEST 8: GET /health accurately reflects model availability and artifact integrity."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()

    assert data["status"] in ["ok", "healthy"]
    assert data["model_active"] is True
    assert data["artifact_integrity_verified"] is True
    assert "model_name" in data
    assert "model_version" in data


def test_9_models_metrics_endpoint_history(auth_headers):
    """TEST 9: GET /models/metrics returns history of all registered model versions."""
    res = client.get("/api/v1/models/metrics", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert "current_model_version" in data
    assert "promoted_model_name" in data
    assert len(data["history"]) > 0


def test_10_model_promotion_updates_active_model(auth_headers):
    """TEST 10: Promoting a candidate model updates active model in registry and APIs."""
    registry = ModelRegistry()
    models = registry.list_models()
    if len(models) >= 2:
        target_version = models[0]["version"]
        res = client.post(f"/api/v1/models/promote/{target_version}", headers=auth_headers)
        assert res.status_code == 200

        # Verify registry active model updated
        new_active = registry.get_active_model_info()
        assert new_active["version"] == target_version

        # Restore original promoted model
        latest_version = models[-1]["version"]
        registry.promote_model(latest_version)
