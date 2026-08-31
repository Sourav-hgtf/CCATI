"""Automated Test Suite for Real-time Churn Prediction Customer Synchronization.

Verifies that real-time predictions, risk tiers, SHAP attributions, and recommendations
are 100% customer-specific and properly synchronized with the selected customer ID.
"""

from fastapi.testclient import TestClient
import pytest
from backend.app.main import app
from backend.app.core.security import create_access_token
from business_engine.risk_scoring import calculate_risk_tier

client = TestClient(app)


@pytest.fixture
def auth_headers():
    token = create_access_token(subject={"sub": "test_user", "email": "test@telecom.com", "role": "Admin"})
    return {"Authorization": f"Bearer {token}"}


def test_1_high_risk_customer_prediction(auth_headers):
    """TEST 1: Select a known HIGH-RISK customer (CUST-10164). Verify high probability & High/Critical tier."""
    res = client.post("/api/v1/predict", json={"customer_id": "CUST-10164"}, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["customer_id"] == "CUST-10164"
    assert data["churn_probability"] >= 0.75
    assert data["risk_tier"] in ["High", "Critical"]
    assert len(data["top_features"]) > 0


def test_2_low_risk_customer_prediction(auth_headers):
    """TEST 2: Select a known LOW-RISK customer (CUST-10006). Verify low probability & Low tier."""
    res = client.post("/api/v1/predict", json={"customer_id": "CUST-10006"}, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["customer_id"] == "CUST-10006"
    assert data["churn_probability"] < 0.25
    assert data["risk_tier"] == "Low"


def test_3_switch_high_to_low_risk_synchronization(auth_headers):
    """TEST 3: Switch HIGH-RISK -> LOW-RISK. Verify that prediction & risk tier change from HIGH to LOW."""
    # Step 1: Predict High Risk
    res_high = client.post("/api/v1/predict", json={"customer_id": "CUST-10164"}, headers=auth_headers)
    assert res_high.json()["risk_tier"] in ["High", "Critical"]
    prob_high = res_high.json()["churn_probability"]

    # Step 2: Predict Low Risk
    res_low = client.post("/api/v1/predict", json={"customer_id": "CUST-10006"}, headers=auth_headers)
    assert res_low.json()["risk_tier"] == "Low"
    prob_low = res_low.json()["churn_probability"]

    # Step 3: Verify strict synchronization and non-stale output
    assert res_low.json()["customer_id"] == "CUST-10006"
    assert prob_low < prob_high
    assert res_low.json()["risk_tier"] != res_high.json()["risk_tier"]


def test_4_switch_low_to_high_risk_synchronization(auth_headers):
    """TEST 4: Switch LOW-RISK -> HIGH-RISK. Verify that prediction & risk tier change from LOW to HIGH."""
    # Step 1: Predict Low Risk
    res_low = client.get("/api/v1/predict/CUST-10008", headers=auth_headers)
    assert res_low.json()["risk_tier"] == "Low"

    # Step 2: Predict High Risk
    res_high = client.get("/api/v1/predict/CUST-10628", headers=auth_headers)
    assert res_high.json()["risk_tier"] in ["High", "Critical"]

    # Step 3: Verify strict update
    assert res_high.json()["customer_id"] == "CUST-10628"
    assert res_high.json()["churn_probability"] > res_low.json()["churn_probability"]


def test_5_distinct_customer_predictions_no_stale_leakage(auth_headers):
    """TEST 5: Verify distinct customer IDs receive distinct customer-specific prediction outputs."""
    res_a = client.post("/api/v1/predict", json={"customer_id": "CUST-10164"}, headers=auth_headers)
    res_b = client.post("/api/v1/predict", json={"customer_id": "CUST-10009"}, headers=auth_headers)

    assert res_a.json()["customer_id"] != res_b.json()["customer_id"]
    assert res_a.json()["churn_probability"] != res_b.json()["churn_probability"]


def test_6_centralized_business_rules_threshold_verification(auth_headers):
    """TEST 6: Verify risk tier calculation adheres strictly to centralized probability thresholds."""
    res_high = client.post("/api/v1/predict", json={"customer_id": "CUST-10164"}, headers=auth_headers)
    prob = res_high.json()["churn_probability"]
    tier = res_high.json()["risk_tier"]
    expected_tier = calculate_risk_tier(prob)

    assert tier == expected_tier


def test_7_rapid_customer_switching_final_id_guarantee(auth_headers):
    """TEST 7: Rapid sequence of predictions (Cust A -> Cust B -> Cust C) guarantees final ID matches."""
    seq = ["CUST-10006", "CUST-10008", "CUST-11267"]
    results = [client.post("/api/v1/predict", json={"customer_id": cid}, headers=auth_headers).json() for cid in seq]

    final_result = results[-1]
    assert final_result["customer_id"] == "CUST-11267"
    assert final_result["risk_tier"] in ["High", "Critical"]


def test_8_invalid_payload_error_handling(auth_headers):
    """TEST 8: Bad payload without customer_id returns 422 Unprocessable Entity, not stale prediction."""
    res = client.post("/api/v1/predict", json={}, headers=auth_headers)
    assert res.status_code == 422
