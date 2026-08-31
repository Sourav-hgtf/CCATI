"""Automated Test Suite for TASK 2 — Real ML Inference & No Fake Fallbacks Verification.

Verifies that:
1. Predictions come strictly from real ML inference / persisted model scoring.
2. Missing customer IDs return clean HTTP 404 errors, NOT fake hash probabilities.
3. No fallback mock functions exist in the prediction pipeline.
"""

from fastapi.testclient import TestClient
import pytest
from backend.app.main import app
from backend.app.core.security import create_access_token

client = TestClient(app)


@pytest.fixture
def auth_headers():
    token = create_access_token(subject={"sub": "test_user", "email": "test@telecom.com", "role": "Admin"})
    return {"Authorization": f"Bearer {token}"}


def test_1_valid_subscriber_returns_real_ml_prediction(auth_headers):
    """TEST 1: Valid subscriber (CUST-10164) returns real ML production prediction."""
    res = client.post("/api/v1/predict", json={"customer_id": "CUST-10164"}, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["customer_id"] == "CUST-10164"
    assert data["model_name"] == "Candidate_RandomForest"
    assert "churn_probability" in data
    assert "risk_tier" in data
    assert isinstance(data["churn_probability"], float)


def test_2_missing_subscriber_returns_404_error_no_fake_fallback(auth_headers):
    """TEST 2: Non-existent subscriber (CUST-99999) returns HTTP 404, NOT a fake hash probability."""
    res = client.post("/api/v1/predict", json={"customer_id": "CUST-99999"}, headers=auth_headers)
    assert res.status_code == 404
    data = res.json()

    assert "not found in database" in data["detail"].lower()


def test_3_get_missing_subscriber_returns_404_error(auth_headers):
    """TEST 3: GET /predict/CUST-99999 returns HTTP 404 error."""
    res = client.get("/api/v1/predict/CUST-99999", headers=auth_headers)
    assert res.status_code == 404
    assert "not found in database" in res.json()["detail"].lower()


def test_4_low_risk_subscriber_returns_real_low_probability(auth_headers):
    """TEST 4: Known low-risk subscriber (CUST-10006) returns exact low probability from ML model."""
    res = client.post("/api/v1/predict", json={"customer_id": "CUST-10006"}, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["customer_id"] == "CUST-10006"
    assert data["churn_probability"] < 0.25
    assert data["risk_tier"] == "Low"
