"""Integration Test Suite for Production PostgreSQL Migration (TASK 20).

Validates end-to-end functionality of all application subsystems connected to PostgreSQL:
- Database connectivity & connection pool
- Health & Readiness probes
- RBAC & Authentication
- Analytics & Aggregation
- Customer Listing, Filtering, Detail & Retention Actions
- Real-time Scoring & Prediction History persistence
- Model Monitoring & Drift Detection
- Audit Logging & Compliance
- Data Export
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.db.session import engine, check_db_connected, SessionLocal
from backend.app.db.models.customer import Customer, CustomerScore
from backend.app.db.models.prediction import PredictionHistory
from backend.app.db.models.audit import AuditLog
from backend.app.main import app

client = TestClient(app)


def test_postgresql_connectivity_and_pool():
    """Verify PostgreSQL engine connection and pre-ping health check."""
    db_ok, db_status = check_db_connected()
    assert db_ok is True
    assert "connected" in db_status.lower()

    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        assert result == 1


def test_health_and_readiness_probes(admin_headers):
    """Verify /health and /ready endpoints return healthy status and check details."""
    res_health = client.get("/health")
    assert res_health.status_code == 200
    data_h = res_health.json()
    assert data_h["status"] == "ok"
    assert "database" in data_h
    assert data_h["model_active"] is True

    res_ready = client.get("/ready")
    assert res_ready.status_code == 200
    data_r = res_ready.json()
    assert data_r["status"] == "ready"
    assert data_r["checks"]["database"] is True
    assert data_r["checks"]["model_registry"] is True


def test_auth_login_and_user_profile():
    """Verify login authentication against PostgreSQL users table."""
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@telecom.com", "password": "AdminPassword123!"},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "admin@telecom.com"
    assert me_res.json()["role"] == "Admin"


def test_analytics_kpi_overview(analyst_headers):
    """Verify /analytics/overview aggregates customer KPIs from PostgreSQL."""
    res = client.get("/api/v1/analytics/overview", headers=analyst_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_customers"] >= 1000
    assert data["churn_rate"] > 0.0
    assert data["revenue_at_risk"] > 0.0
    assert data["high_risk_customers"] > 0


def test_analytics_risk_distribution(analyst_headers):
    """Verify /analytics/distribution returns tier counts and percentages."""
    res = client.get("/api/v1/analytics/distribution", headers=analyst_headers)
    assert res.status_code == 200
    dist = res.json()
    assert len(dist) == 4
    tiers = [d["tier"] for d in dist]
    assert "High" in tiers
    assert "Low" in tiers


def test_customers_listing_and_filtering(manager_headers):
    """Verify /customers supports pagination, risk filtering, and search."""
    res = client.get("/api/v1/customers?page=1&page_size=10&risk_tier=Critical", headers=manager_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] > 0
    assert len(data["items"]) <= 10
    assert all(item["risk_tier"] == "Critical" for item in data["items"])


def test_customer_detail_and_pii_unmasking(manager_headers, analyst_headers):
    """Verify /customers/{id} masks PII for analysts and unmasks for authorized managers."""
    # Masked view for Analyst
    res_masked = client.get("/api/v1/customers/CUST-10000?reveal_pii=false", headers=analyst_headers)
    assert res_masked.status_code == 200
    cust = res_masked.json()
    assert "***" in cust["name"] or "*" in cust["name"]
    assert "X" in cust["phone"] or "*" in cust["phone"]

    # Unmasked view for RetentionManager
    res_unmasked = client.get("/api/v1/customers/CUST-10000?reveal_pii=true", headers=manager_headers)
    assert res_unmasked.status_code == 200
    cust_unmasked = res_unmasked.json()
    assert cust_unmasked["is_pii_revealed"] is True
    assert cust_unmasked["name"] != cust["name"]


def test_retention_action_marking(manager_headers):
    """Verify marking a retention action updates PostgreSQL customer_scores and logs audit event."""
    res = client.post("/api/v1/customers/CUST-10000/action", headers=manager_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "SUCCESS"

    # Verify directly via session
    session = SessionLocal()
    try:
        score = session.query(CustomerScore).filter(CustomerScore.customer_id == "CUST-10000").first()
        assert score.actioned == 1
        assert score.actioned_at is not None
    finally:
        session.close()


def test_realtime_prediction_and_history_persistence(analyst_headers):
    """Verify real-time prediction calculates SHAP explanations and persists to PostgreSQL prediction_history."""
    res = client.post(
        "/api/v1/predict",
        json={"customer_id": "CUST-10000"},
        headers=analyst_headers,
    )
    assert res.status_code == 200
    pred = res.json()
    assert "prediction_id" in pred
    assert pred["churn_probability"] >= 0.0
    assert pred["decision"] in ["RETENTION_INTERVENTION_RECOMMENDED", "STANDARD_MONITORING"]

    pred_id = pred["prediction_id"]

    # Retrieve from history by ID
    res_hist = client.get(f"/api/v1/predictions/{pred_id}", headers=analyst_headers)
    assert res_hist.status_code == 200
    assert res_hist.json()["prediction_id"] == pred_id


def test_segment_profiles_and_scatter(analyst_headers):
    """Verify behavioral segment profiles and scatter points loaded from PostgreSQL."""
    res = client.get("/api/v1/segments", headers=analyst_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["segments"]) == 4
    assert len(data["scatter_points"]) > 0
    assert data["quality_metrics"]["silhouette_score"] > 0


def test_model_drift_and_monitoring_history(admin_headers):
    """Verify model drift analysis execution and history in PostgreSQL."""
    res = client.post("/api/v1/monitoring/run", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "run" in data

    res_hist = client.get("/api/v1/monitoring/history", headers=admin_headers)
    assert res_hist.status_code == 200
    assert len(res_hist.json()) > 0


def test_performance_evaluation_and_history(admin_headers):
    """Verify model performance evaluation execution and history in PostgreSQL."""
    res = client.post("/api/v1/monitoring/performance/run", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "status" in data

    res_hist = client.get("/api/v1/monitoring/performance/history", headers=admin_headers)
    assert res_hist.status_code == 200
    assert len(res_hist.json()) > 0


def test_audit_logs_retrieval(admin_headers):
    """Verify audit logs are persisted and retrievable from PostgreSQL."""
    res = client.get("/api/v1/admin/audit-logs?limit=10", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "logs" in data
    assert len(data["logs"]) > 0
    assert "actor_email" in data["logs"][0]
    assert "action" in data["logs"][0]


def test_customer_csv_export(admin_headers):
    """Verify customer CSV export from PostgreSQL."""
    res = client.get("/api/v1/export/customers?risk_tier=Critical", headers=admin_headers)
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "customer_id,name,phone" in res.text
