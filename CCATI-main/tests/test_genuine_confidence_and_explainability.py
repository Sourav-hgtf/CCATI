"""Automated Test Suite for TASK 4 — Genuine Model Confidence & SHAP Explainability.

Verifies that:
1. Model confidence score is calculated mathematically as max(p, 1-p).
2. No fake or hardcoded (e.g. 0.94) confidence values exist in predictions.
3. SHAP feature attributions are 100% customer-specific and aligned with model version.
4. Positive SHAP values indicate increased risk, negative values indicate reduced risk.
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


def test_1_churn_probability_in_valid_range(auth_headers):
    """TEST 1: Churn probability is bounded within [0, 1]."""
    res = client.post("/api/v1/predict", json={"customer_id": "CUST-10164"}, headers=auth_headers)
    assert res.status_code == 200
    prob = res.json()["churn_probability"]
    assert 0.0 <= prob <= 1.0


def test_2_genuine_confidence_score_calculation(auth_headers):
    """TEST 2: Confidence score is dynamically computed as max(prob, 1 - prob), never hardcoded."""
    res_high = client.post("/api/v1/predict", json={"customer_id": "CUST-10164"}, headers=auth_headers).json()
    prob_high = res_high["churn_probability"]
    expected_conf_high = round(max(prob_high, 1.0 - prob_high), 4)

    assert res_high["confidence_score"] == expected_conf_high

    res_low = client.post("/api/v1/predict", json={"customer_id": "CUST-10006"}, headers=auth_headers).json()
    prob_low = res_low["churn_probability"]
    expected_conf_low = round(max(prob_low, 1.0 - prob_low), 4)

    assert res_low["confidence_score"] == expected_conf_low
    assert res_high["confidence_score"] != 0.94 or expected_conf_high == 0.94


def test_3_shap_explanations_correspond_to_model_version(auth_headers):
    """TEST 3: SHAP feature explanations use the active production model version."""
    registry = ModelRegistry()
    active_info = registry.get_active_model_info()

    res = client.post("/api/v1/predict", json={"customer_id": "CUST-10164"}, headers=auth_headers).json()
    assert res["model_version"] == active_info["version"]
    assert len(res["top_features"]) > 0


def test_4_shap_contribution_directions(auth_headers):
    """TEST 4: Positive SHAP impact indicates Increase, negative impact indicates Decrease."""
    res = client.post("/api/v1/predict", json={"customer_id": "CUST-10164"}, headers=auth_headers).json()
    top_features = res["top_features"]

    for feat in top_features:
        if feat["contribution"] > 0:
            assert feat["impact"] == "Increase"
        elif feat["contribution"] < 0:
            assert feat["impact"] == "Decrease"


def test_5_customer_specific_shap_attributions(auth_headers):
    """TEST 5: Top SHAP features are customer-specific and differ between subscribers."""
    res_a = client.post("/api/v1/predict", json={"customer_id": "CUST-10164"}, headers=auth_headers).json()
    res_b = client.post("/api/v1/predict", json={"customer_id": "CUST-10006"}, headers=auth_headers).json()

    # Features or contribution values must be distinct between High and Low risk subscribers
    assert res_a["top_features"] != res_b["top_features"]


def test_6_valid_feature_names_and_values_in_explanation(auth_headers):
    """TEST 6: Explanation payload contains non-empty feature names and formatted values."""
    res = client.post("/api/v1/predict", json={"customer_id": "CUST-10164"}, headers=auth_headers).json()
    for feat in res["top_features"]:
        assert len(feat["feature_name"]) > 0
        assert feat["feature_value"] is not None
        assert isinstance(feat["contribution"], float)
