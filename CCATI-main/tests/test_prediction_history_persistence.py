"""Automated Test Suite for TASK 6 — Production Prediction History & Persistent Inference Records.

Verifies that:
1. Every successful real-time prediction generates a unique prediction_id and persists in prediction_history.
2. GET /predictions/{prediction_id} retrieves historical prediction snapshot without rerunning ML model.
3. GET /customers/{customer_id}/predictions retrieves subscriber chronological history.
4. GET /predictions/history supports server-side pagination and risk tier filtering.
5. Multiple predictions for the same customer preserve distinct historical snapshots.
"""

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


def test_1_prediction_generates_id_and_persists_record(auth_headers):
    """TEST 1: Real-time prediction returns prediction_id and persists to database."""
    res = client.post("/api/v1/predict", json={"customer_id": "CUST-10164"}, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert "prediction_id" in data
    assert data["prediction_id"].startswith("pred-")
    assert data["customer_id"] == "CUST-10164"


def test_2_get_prediction_by_id_retrieves_snapshot(auth_headers):
    """TEST 2: GET /predictions/{prediction_id} retrieves exact historical snapshot."""
    pred_res = client.post("/api/v1/predict", json={"customer_id": "CUST-10164"}, headers=auth_headers).json()
    pred_id = pred_res["prediction_id"]

    res = client.get(f"/api/v1/predictions/{pred_id}", headers=auth_headers)
    assert res.status_code == 200
    hist_item = res.json()

    assert hist_item["prediction_id"] == pred_id
    assert hist_item["customer_id"] == "CUST-10164"
    assert hist_item["churn_probability"] == pred_res["churn_probability"]
    assert hist_item["risk_tier"] == pred_res["risk_tier"]
    assert hist_item["model_name"] == pred_res["model_name"]
    assert hist_item["model_version"] == pred_res["model_version"]


def test_3_get_customer_prediction_history(auth_headers):
    """TEST 3: GET /customers/{customer_id}/predictions returns customer's prediction history."""
    client.post("/api/v1/predict", json={"customer_id": "CUST-10006"}, headers=auth_headers)
    res = client.get("/api/v1/customers/CUST-10006/predictions", headers=auth_headers)

    assert res.status_code == 200
    history = res.json()

    assert isinstance(history, list)
    assert len(history) >= 1
    for item in history:
        assert item["customer_id"] == "CUST-10006"


def test_4_paginated_prediction_history(auth_headers):
    """TEST 4: GET /predictions/history supports pagination parameters."""
    res = client.get("/api/v1/predictions/history?page=1&page_size=5", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert "items" in data
    assert "total" in data
    assert data["page"] == 1
    assert data["page_size"] == 5
    assert len(data["items"]) <= 5


def test_5_prediction_history_filtering(auth_headers):
    """TEST 5: Filtering history by risk_tier returns matching records."""
    res = client.get("/api/v1/predictions/history?risk_tier=High", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    for item in data["items"]:
        assert item["risk_tier"] == "High"


def test_6_invalid_prediction_id_returns_404(auth_headers):
    """TEST 6: Invalid prediction_id returns 404 NOT FOUND error."""
    res = client.get("/api/v1/predictions/pred-invalid-id-9999", headers=auth_headers)
    assert res.status_code == 404


def test_7_multiple_predictions_preserve_distinct_snapshots(auth_headers):
    """TEST 7: Sequential predictions for same customer create distinct historical records."""
    res1 = client.post("/api/v1/predict", json={"customer_id": "CUST-10164"}, headers=auth_headers).json()
    res2 = client.post("/api/v1/predict", json={"customer_id": "CUST-10164"}, headers=auth_headers).json()

    assert res1["prediction_id"] != res2["prediction_id"]

    cust_history = client.get("/api/v1/customers/CUST-10164/predictions", headers=auth_headers).json()
    pred_ids = [item["prediction_id"] for item in cust_history]

    assert res1["prediction_id"] in pred_ids
    assert res2["prediction_id"] in pred_ids
