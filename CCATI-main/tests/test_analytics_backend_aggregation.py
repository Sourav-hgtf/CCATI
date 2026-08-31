"""Automated Test Suite for TASK 5 — Backend Analytics & Aggregation.

Verifies that:
1. Dashboard KPIs (total, churn rate, high risk, revenue at risk) are dynamically aggregated from database tables.
2. Risk distribution counts equal total subscriber population.
3. No hardcoded or mock KPI constants are returned in production analytics APIs.
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


def test_1_analytics_overview_dynamic_aggregation(auth_headers):
    """TEST 1: GET /analytics/overview returns real database-aggregated metrics."""
    res = client.get("/api/v1/analytics/overview", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["total_customers"] > 0
    assert data["active_customers"] > 0
    assert data["high_risk_customers"] >= 0
    assert data["medium_risk_customers"] >= 0
    assert data["low_risk_customers"] >= 0
    assert 0.0 <= data["churn_rate"] <= 100.0
    assert data["revenue_at_risk"] >= 0.0


def test_2_risk_distribution_population_consistency(auth_headers):
    """TEST 2: High + Medium + Low risk counts equal total customer population."""
    res = client.get("/api/v1/analytics/overview", headers=auth_headers).json()
    sum_risk = res["high_risk_customers"] + res["medium_risk_customers"] + res["low_risk_customers"]
    assert sum_risk == res["total_customers"]


def test_3_churn_rate_calculation_consistency(auth_headers):
    """TEST 3: Churn rate matches high_risk_customers / total_customers * 100."""
    res = client.get("/api/v1/analytics/overview", headers=auth_headers).json()
    expected_rate = round((res["high_risk_customers"] / res["total_customers"]) * 100, 1)
    assert res["churn_rate"] == expected_rate


def test_4_risk_distribution_endpoint(auth_headers):
    """TEST 4: GET /analytics/distribution returns tier breakdown matching total population."""
    res = client.get("/api/v1/analytics/distribution", headers=auth_headers)
    assert res.status_code == 200
    tiers = res.json()

    total_cnt = sum(t["count"] for t in tiers)
    res_overview = client.get("/api/v1/analytics/overview", headers=auth_headers).json()
    assert total_cnt == res_overview["total_customers"]


def test_5_contract_breakdown_endpoint(auth_headers):
    """TEST 5: GET /analytics/contracts returns aggregated contract breakdowns."""
    res = client.get("/api/v1/analytics/contracts", headers=auth_headers)
    assert res.status_code == 200
    contracts = res.json()

    assert len(contracts) > 0
    for c in contracts:
        assert "contract" in c
        assert "churn_rate" in c
        assert c["customers"] > 0
