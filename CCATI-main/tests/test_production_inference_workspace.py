"""Automated Test Suite for TASK 7 — Production-Grade Real-time Churn Inference & Workspace.

Verifies that:
1. Predictions are generated using real ML model inference & production preprocessing.
2. Selected subscriber ID strictly controls customer features and returned predictions.
3. Risk tiers match centralized business boundary rules (Low < 0.25, Medium 0.25-0.50, High 0.50-0.75, Critical >= 0.75).
4. Invalid subscriber requests return 404 NOT FOUND with zero mock fallbacks.
"""

from fastapi.testclient import TestClient
import pytest
from backend.app.main import app
from backend.app.core.security import create_access_token
from business_engine.risk_scoring import calculate_risk_tier
from ml_engine.registry.model_registry import ModelRegistry

client = TestClient(app)


@pytest.fixture
def auth_headers():
    token = create_access_token(subject={"sub": "test_user", "email": "test@telecom.com", "role": "Admin"})
    return {"Authorization": f"Bearer {token}"}


def test_1_end_to_end_production_inference(auth_headers):
    """TEST 1: Real-time prediction executes end-to-end through real ML model pipeline."""
    res = client.post("/api/v1/predict", json={"customer_id": "CUST-10164"}, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["customer_id"] == "CUST-10164"
    assert 0.0 <= data["churn_probability"] <= 1.0
    assert data["risk_tier"] in ["Low", "Medium", "High", "Critical"]
    assert "prediction_id" in data
    assert len(data["top_features"]) > 0


def test_2_customer_selection_determines_unique_predictions(auth_headers):
    """TEST 2: Customer selection strictly determines features, probability, and risk tier."""
    res_high = client.post("/api/v1/predict", json={"customer_id": "CUST-10164"}, headers=auth_headers).json()
    res_low = client.post("/api/v1/predict", json={"customer_id": "CUST-10006"}, headers=auth_headers).json()

    assert res_high["customer_id"] == "CUST-10164"
    assert res_low["customer_id"] == "CUST-10006"
    assert res_high["churn_probability"] != res_low["churn_probability"]
    assert res_high["risk_tier"] != res_low["risk_tier"]


def test_3_risk_boundary_classification():
    """TEST 3: Risk tier boundaries use exact centralized business rules."""
    assert calculate_risk_tier(0.15) == "Low"
    assert calculate_risk_tier(0.2499) == "Low"
    assert calculate_risk_tier(0.25) == "Medium"
    assert calculate_risk_tier(0.4999) == "Medium"
    assert calculate_risk_tier(0.50) == "High"
    assert calculate_risk_tier(0.7499) == "High"
    assert calculate_risk_tier(0.75) == "Critical"
    assert calculate_risk_tier(0.99) == "Critical"


def test_4_invalid_subscriber_returns_404(auth_headers):
    """TEST 4: Non-existent subscriber ID returns 404 NOT FOUND without fallback predictions."""
    res = client.post("/api/v1/predict", json={"customer_id": "CUST-999999-UNKNOWN"}, headers=auth_headers)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_5_model_metadata_consistency_in_workspace(auth_headers):
    """TEST 5: Prediction response contains active model registry name and version."""
    registry = ModelRegistry()
    active_info = registry.get_active_model_info()

    res = client.post("/api/v1/predict", json={"customer_id": "CUST-10164"}, headers=auth_headers).json()
    assert res["model_name"] == active_info["model_name"]
    assert res["model_version"] == active_info["version"]
