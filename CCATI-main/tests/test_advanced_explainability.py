"""Comprehensive Test Suite for Task 13: Advanced Model Explainability & Decision Transparency.

Validates:
1. SHAP Explainer compatibility with the active production model artifact from ModelRegistry.
2. Human-readable feature name mapping (no raw technical names like 'feature_17' or 'tenure_months_scaled').
3. Business-oriented feature value formatting (percentages, currency, counts, units).
4. Top positive drivers (risk escalators) and top negative drivers (protective factors) separation and ordering.
5. Decision transparency calculation (threshold 0.50, decision code, and human-readable decision reason).
6. API schema validation for real-time inference and prediction history.
7. Edge-case and fallback handling (graceful degradation with 'UNAVAILABLE' status).
8. Performance / latency checks with explainer caching.
"""

import json
import time
import pytest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.security import create_access_token
from ml_engine.registry.model_registry import ModelRegistry
from ml_engine.pipelines.explainability import (
    compute_shap_explanations,
    get_human_readable_feature_info,
    format_feature_value,
    _get_or_create_explainer,
    FEATURE_METADATA_MAP,
)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def auth_headers():
    token = create_access_token(subject={"sub": "test_user", "email": "test@telecom.com", "role": "Admin"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def production_model_and_metadata():
    registry = ModelRegistry()
    model, metadata = registry.get_model()
    assert model is not None, "A promoted production model must exist in ModelRegistry."
    return model, metadata


# --------------------------------------------------------------------------
# 1. Active Production Model & Explainer Compatibility
# --------------------------------------------------------------------------

def test_1_explainer_uses_same_production_model_artifact(production_model_and_metadata):
    """Ensure SHAP explanations are computed from the identical promoted production model."""
    model, metadata = production_model_and_metadata

    # Load sample features
    sample_df = pd.DataFrame([{
        "tenure_months": 12,
        "monthly_charges": 750.0,
        "total_charges": 9000.0,
        "call_minutes_m1": 300.0,
        "call_minutes_m2": 280.0,
        "call_minutes_m3": 250.0,
        "data_gb_m1": 15.0,
        "data_gb_m2": 14.0,
        "data_gb_m3": 12.0,
        "sms_count_m1": 50,
        "sms_count_m2": 45,
        "sms_count_m3": 40,
        "support_calls_m1": 2,
        "support_calls_m2": 1,
        "support_calls_m3": 0,
        "payment_delays_m1": 0,
        "payment_delays_m2": 0,
        "payment_delays_m3": 0,
        "contract_type": "Month-to-Month",
        "payment_method": "Credit Card",
        "plan_tier": "Postpaid Basic",
        "internet_service": "Fiber",
        "region": "North",
    }])

    explanations = compute_shap_explanations(
        model_pipeline=model,
        X_df=sample_df,
        top_n=5
    )

    assert len(explanations) == 1
    exp = explanations[0]
    assert exp["explanation_status"] == "AVAILABLE"
    assert "top_positive_drivers" in exp
    assert "top_negative_drivers" in exp
    assert "all_drivers" in exp
    assert 0.0 <= exp["base_value"] <= 1.0


# --------------------------------------------------------------------------
# 2. Human-Readable Feature Mapping & Value Formatting
# --------------------------------------------------------------------------

def test_2_feature_metadata_mapping():
    """Verify that technical and one-hot encoded features map to clean business names and categories."""
    base_feat, display_name, category = get_human_readable_feature_info("usage_drop_call_pct")
    assert base_feat == "usage_drop_call_pct"
    assert display_name == "Voice Usage Drop (%)"
    assert category == "Usage & Engagement"

    base_cat, display_name_cat, category_cat = get_human_readable_feature_info("cat__contract_type_Month-to-Month")
    assert base_cat == "contract_type"
    assert display_name_cat == "Contract Type (Month-to-Month)"
    assert category_cat == "Contract & Plan"

    # Check value formatting
    assert format_feature_value("monthly_charges", 799.5) == "₹799.50"
    assert format_feature_value("usage_drop_call_pct", 0.354) == "35.4%"
    assert format_feature_value("support_calls_m1", 4) == "4 calls"
    assert format_feature_value("tenure_months", 18) == "18 months"


# --------------------------------------------------------------------------
# 3. Top Positive and Negative Driver Separation & Ordering
# --------------------------------------------------------------------------

def test_3_driver_separation_and_magnitude_ordering(production_model_and_metadata):
    """Verify positive drivers (increasing churn) and negative drivers (reducing churn) are separated and sorted."""
    model, metadata = production_model_and_metadata

    sample_df = pd.DataFrame([{
        "tenure_months": 2,
        "monthly_charges": 999.0,
        "total_charges": 1998.0,
        "call_minutes_m1": 100.0,
        "call_minutes_m2": 300.0,
        "call_minutes_m3": 500.0,
        "data_gb_m1": 2.0,
        "data_gb_m2": 10.0,
        "data_gb_m3": 20.0,
        "sms_count_m1": 10,
        "sms_count_m2": 30,
        "sms_count_m3": 50,
        "support_calls_m1": 5,
        "support_calls_m2": 2,
        "support_calls_m3": 0,
        "payment_delays_m1": 2,
        "payment_delays_m2": 1,
        "payment_delays_m3": 0,
        "contract_type": "Month-to-Month",
        "payment_method": "Electronic Check",
        "plan_tier": "Postpaid Premium",
        "internet_service": "Fiber",
        "region": "West",
    }])

    explanations = compute_shap_explanations(model_pipeline=model, X_df=sample_df, top_n=5)
    exp = explanations[0]

    pos_drivers = exp["top_positive_drivers"]
    neg_drivers = exp["top_negative_drivers"]

    # All positive drivers must have contribution > 0
    for d in pos_drivers:
        assert d["contribution"] > 0
        assert d["impact"] == "Increase"
        assert d["direction"] == "INCREASES_CHURN"
        assert "Increases" in d["effect"]

    # All negative drivers must have contribution < 0
    for d in neg_drivers:
        assert d["contribution"] < 0
        assert d["impact"] == "Decrease"
        assert d["direction"] == "DECREASES_CHURN"
        assert "Reduces" in d["effect"]

    # Positive drivers must be sorted descending by contribution
    pos_contribs = [d["contribution"] for d in pos_drivers]
    assert pos_contribs == sorted(pos_contribs, reverse=True)

    # Negative drivers must be sorted by magnitude (most protective first)
    neg_contribs = [d["contribution"] for d in neg_drivers]
    assert neg_contribs == sorted(neg_contribs)


# --------------------------------------------------------------------------
# 4. Real-time Inference API Contract & Decision Transparency
# --------------------------------------------------------------------------

def test_4_predict_endpoint_returns_decision_transparency(client, auth_headers):
    """Test /api/v1/predict response structure for decision transparency and explanations."""
    response = client.post("/api/v1/predict", json={"customer_id": "CUST-10164"}, headers=auth_headers)
    assert response.status_code == 200, f"Expected 200, got: {response.text}"

    data = response.json()

    # Core Prediction & Confidence
    assert "churn_probability" in data
    assert 0.0 <= data["churn_probability"] <= 1.0
    assert "confidence_score" in data
    assert 0.5 <= data["confidence_score"] <= 1.0
    assert "risk_tier" in data

    # Decision Transparency Fields (TASK 13)
    assert data["threshold"] == 0.50
    if data["churn_probability"] >= 0.50:
        assert data["decision"] == "RETENTION_INTERVENTION_RECOMMENDED"
        assert "exceeds" in data["decision_reason"]
    else:
        assert data["decision"] == "STANDARD_MONITORING"
        assert "is below" in data["decision_reason"]

    # Detailed Explanation Object
    assert "explanation" in data
    exp = data["explanation"]
    assert exp["explanation_status"] in ["AVAILABLE", "UNAVAILABLE"]
    if exp["explanation_status"] == "AVAILABLE":
        assert isinstance(exp["top_positive_drivers"], list)
        assert isinstance(exp["top_negative_drivers"], list)
        assert isinstance(exp["all_drivers"], list)
        assert "disclaimer" in exp
        assert "causation" in exp["disclaimer"].lower()


# --------------------------------------------------------------------------
# 5. Prediction History Persistence & Customer History Retrieval
# --------------------------------------------------------------------------

def test_5_prediction_history_schema(client, auth_headers):
    """Test /api/v1/predictions/history endpoint returns structured explanation fields."""
    response = client.get("/api/v1/predictions/history?page=1&page_size=5", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert len(data["items"]) > 0

    item = data["items"][0]
    assert "prediction_id" in item
    assert "churn_probability" in item
    assert "threshold" in item
    assert "decision" in item
    assert "explanation" in item
    assert item["explanation"]["explanation_status"] in ["AVAILABLE", "UNAVAILABLE"]


# --------------------------------------------------------------------------
# 6. Fallback & Graceful Degradation on Invalid / Missing Explanation
# --------------------------------------------------------------------------

def test_6_fallback_on_unsupported_model():
    """Verify compute_shap_explanations returns UNAVAILABLE when explanation cannot be computed."""
    class DummyModel:
        pass

    dummy_df = pd.DataFrame([{"feat_a": 1}])
    explanations = compute_shap_explanations(model_pipeline=DummyModel(), X_df=dummy_df)
    assert len(explanations) == 1
    assert explanations[0]["explanation_status"] == "UNAVAILABLE"
    assert "unavailable" in explanations[0]["summary"].lower()


# --------------------------------------------------------------------------
# 7. Latency and Explainer Caching Performance
# --------------------------------------------------------------------------

def test_7_explainer_caching_performance(production_model_and_metadata):
    """Verify that cached explainer delivers low-latency explanations."""
    model, metadata = production_model_and_metadata

    sample_df = pd.DataFrame([{
        "tenure_months": 24,
        "monthly_charges": 500.0,
        "total_charges": 12000.0,
        "call_minutes_m1": 200.0,
        "call_minutes_m2": 200.0,
        "call_minutes_m3": 200.0,
        "data_gb_m1": 10.0,
        "data_gb_m2": 10.0,
        "data_gb_m3": 10.0,
        "sms_count_m1": 20,
        "sms_count_m2": 20,
        "sms_count_m3": 20,
        "support_calls_m1": 0,
        "support_calls_m2": 0,
        "support_calls_m3": 0,
        "payment_delays_m1": 0,
        "payment_delays_m2": 0,
        "payment_delays_m3": 0,
        "contract_type": "Two Year",
        "payment_method": "Bank Transfer",
        "plan_tier": "Postpaid Standard",
        "internet_service": "DSL",
        "region": "South",
    }])

    # First call (warm cache)
    compute_shap_explanations(model_pipeline=model, X_df=sample_df)

    # Second call (must be fast)
    t0 = time.time()
    for _ in range(5):
        compute_shap_explanations(model_pipeline=model, X_df=sample_df)
    elapsed = time.time() - t0

    avg_latency = elapsed / 5.0
    # Average latency per customer explanation should be well under 200ms
    assert avg_latency < 0.20, f"Average explanation latency {avg_latency*1000:.1f}ms exceeds 200ms threshold."
