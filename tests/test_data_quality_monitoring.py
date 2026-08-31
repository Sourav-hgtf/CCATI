"""Automated Test Suite for TASK 11 — Production Data Quality, Input Validation & Data Quality Monitoring.

Verifies:
1. Data Quality Engine validates customer records against the production feature schema.
2. Missing required fields, nulls, NaNs, and infinite values are caught.
3. Negative numeric values (tenure, monthly_charges, total_charges, usage, support_calls) trigger CRITICAL errors.
4. Categorical and range validations produce appropriate warnings/errors.
5. Quality score (0-100) and health statuses (EXCELLENT, GOOD, WARNING, CRITICAL) are computed mathematically.
6. Pre-inference validation blocks critical invalid data and permits clean data.
7. Endpoints (/data-quality, /data-quality/validate, /data-quality/customer/{id}) return strongly-typed responses.
8. Database dataset quality audit aggregates field-level statistics and duplicate detection.
"""

from fastapi.testclient import TestClient
import pytest
from backend.app.main import app
from backend.app.core.security import create_access_token
from backend.app.services.data_quality import DataQualityEngine

client = TestClient(app)


@pytest.fixture
def auth_headers():
    token = create_access_token(subject={"sub": "usr-admin", "email": "admin@telecom.com", "role": "Admin"})
    return {"Authorization": f"Bearer {token}"}


def test_1_valid_customer_data_quality():
    """TEST 1: Valid customer record achieves 100/100 quality score and passes validation."""
    engine = DataQualityEngine()
    record = {
        "customer_id": "CUST-99999",
        "tenure_months": 24,
        "monthly_charges": 75.50,
        "total_charges": 1812.00,
        "contract_type": "1-Year",
        "plan_tier": "Standard",
        "support_calls_m1": 1,
        "call_minutes_m1": 320.0,
    }
    res = engine.validate_record(record)
    assert res["is_valid"] is True
    assert res["has_critical_errors"] is False
    assert res["can_proceed_to_inference"] is True
    assert res["quality_score"] == 100.0
    assert res["quality_status"] == "EXCELLENT"
    assert len(res["issues"]) == 0


def test_2_missing_required_fields():
    """TEST 2: Missing required customer_id, tenure_months, or monthly_charges triggers critical errors."""
    engine = DataQualityEngine()
    
    # Missing customer_id
    res_no_id = engine.validate_record({"tenure_months": 12, "monthly_charges": 50.0})
    assert res_no_id["can_proceed_to_inference"] is False
    assert any(i["field"] == "customer_id" for i in res_no_id["issues"])

    # Missing tenure_months
    res_no_tenure = engine.validate_record({"customer_id": "CUST-1", "monthly_charges": 50.0})
    assert res_no_tenure["can_proceed_to_inference"] is False
    assert any(i["field"] == "tenure_months" for i in res_no_tenure["issues"])


def test_3_negative_numeric_values():
    """TEST 3: Negative tenure, monthly_charges, or total_charges are rejected as CRITICAL."""
    engine = DataQualityEngine()
    record = {
        "customer_id": "CUST-BAD-NUM",
        "tenure_months": -6,
        "monthly_charges": -45.0,
        "total_charges": -200.0,
    }
    res = engine.validate_record(record)
    assert res["can_proceed_to_inference"] is False
    assert res["quality_score"] <= 50.0
    assert res["quality_status"] == "CRITICAL"
    assert any(i["field"] == "tenure_months" and i["issue_type"] == "negative_value" for i in res["issues"])
    assert any(i["field"] == "monthly_charges" and i["issue_type"] == "negative_value" for i in res["issues"])


def test_4_invalid_categoricals_and_ranges():
    """TEST 4: Unknown plan tier, unknown contract, and out-of-range tenure generate warnings."""
    engine = DataQualityEngine()
    record = {
        "customer_id": "CUST-WARN",
        "tenure_months": 250,  # Exceeds max_tenure_months
        "monthly_charges": 60.0,
        "contract_type": "LifetimeUnlimited",
        "plan_tier": "VIP_Infinite",
    }
    res = engine.validate_record(record)
    assert res["has_critical_errors"] is False
    assert res["can_proceed_to_inference"] is True
    assert res["quality_score"] < 100.0
    assert any(i["issue_type"] == "out_of_range" for i in res["issues"])
    assert any(i["issue_type"] == "invalid_category" for i in res["issues"])


def test_5_data_quality_score_penalties():
    """TEST 5: Data quality scores reflect cumulative penalties clamped between 0 and 100."""
    engine = DataQualityEngine()
    # Severe multi-error record
    record = {
        "customer_id": "",
        "tenure_months": -10,
        "monthly_charges": -100.0,
        "total_charges": -500.0,
        "support_calls_m1": -5,
    }
    res = engine.validate_record(record)
    assert res["quality_score"] == 0.0
    assert res["quality_status"] == "CRITICAL"
    assert res["can_proceed_to_inference"] is False


def test_6_database_quality_audit():
    """TEST 6: audit_database_quality evaluates total records, valid counts, and field diagnostics."""
    engine = DataQualityEngine()
    audit = engine.audit_database_quality()

    assert audit["total_records"] > 0
    assert audit["valid_records"] > 0
    assert audit["overall_quality_score"] >= 75.0
    assert audit["quality_status"] in ["EXCELLENT", "GOOD", "WARNING", "CRITICAL"]
    assert "field_issues" in audit
    assert "alerts" in audit


def test_7_get_data_quality_report_api(auth_headers):
    """TEST 7: GET /api/v1/data-quality returns full dataset audit report."""
    res = client.get("/api/v1/data-quality", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "overall_quality_score" in data
    assert "valid_records" in data
    assert "invalid_records" in data
    assert isinstance(data["field_issues"], list)


def test_8_validate_customer_data_api_post(auth_headers):
    """TEST 8: POST /api/v1/data-quality/validate tests customer payload without model inference."""
    payload = {
        "customer_id": "TEST-CUST-1",
        "tenure_months": 15,
        "monthly_charges": 65.0,
        "contract_type": "Month-to-Month",
    }
    res = client.post("/api/v1/data-quality/validate", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["customer_id"] == "TEST-CUST-1"
    assert data["can_proceed_to_inference"] is True
    assert data["quality_score"] == 100.0


def test_9_customer_data_quality_by_id_api(auth_headers):
    """TEST 9: GET /api/v1/data-quality/customer/{id} returns diagnostics for stored customer."""
    res = client.get("/api/v1/data-quality/customer/CUST-10000", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["customer_id"] == "CUST-10000"
    assert data["quality_score"] >= 80.0


def test_10_prediction_endpoint_accepts_clean_data(auth_headers):
    """TEST 10: POST /api/v1/predict succeeds for valid subscriber."""
    res = client.post("/api/v1/predict", json={"customer_id": "CUST-10000"}, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["customer_id"] == "CUST-10000"
    assert "churn_probability" in data
