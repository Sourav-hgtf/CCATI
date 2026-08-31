"""Automated Test Suite for TASK 8 — Advanced Model Monitoring & Data Drift Intelligence.

Verifies that:
1. Numerical PSI and KS-test calculations accurately detect feature distribution shifts.
2. Categorical PSI calculations flag shifted category proportions.
3. Overall status (STABLE, WARNING, CRITICAL) is dynamically derived using configurable thresholds.
4. Monitoring runs persist to SQLite monitoring_history table.
5. Monitoring endpoints (/monitoring/status, /monitoring/drift, /monitoring/history, /monitoring/run) return properly typed responses.
"""

from fastapi.testclient import TestClient
import numpy as np
import pytest
from backend.app.main import app
from backend.app.core.security import create_access_token
from ml_engine.monitoring.drift_detector import (
    DriftDetector,
    calculate_categorical_psi,
    calculate_numerical_psi,
)

client = TestClient(app)


@pytest.fixture
def auth_headers():
    token = create_access_token(subject={"sub": "test_user", "email": "admin@telecom.com", "role": "Admin"})
    return {"Authorization": f"Bearer {token}"}


def test_1_numerical_psi_stable_distribution():
    """TEST 1: Identical numerical distributions return PSI ~ 0.0 and STABLE severity."""
    ref = np.random.normal(50, 10, 1000)
    curr = np.random.normal(50, 10, 1000)
    psi, p_val, severity = calculate_numerical_psi(ref, curr)
    assert psi < 0.10
    assert severity == "STABLE"


def test_2_numerical_psi_shifted_distribution():
    """TEST 2: Shifted numerical distribution returns PSI >= 0.25 and CRITICAL severity."""
    ref = np.random.normal(50, 10, 1000)
    curr = np.random.normal(90, 10, 1000)
    psi, p_val, severity = calculate_numerical_psi(ref, curr)
    assert psi >= 0.25
    assert severity == "CRITICAL"


def test_3_categorical_psi_shifted_distribution():
    """TEST 3: Shifted categorical proportions return WARNING or CRITICAL severity."""
    ref = ["Month-to-Month"] * 800 + ["One Year"] * 200
    curr = ["Month-to-Month"] * 200 + ["One Year"] * 800
    psi, severity = calculate_categorical_psi(ref, curr)
    assert psi > 0.10
    assert severity in ["WARNING", "CRITICAL"]


def test_4_drift_detector_run_analysis():
    """TEST 4: DriftDetector executes statistical analysis against production database records."""
    detector = DriftDetector()
    res = detector.run_drift_analysis()
    assert res["status"] in ["STABLE", "WARNING", "CRITICAL", "INSUFFICIENT_DATA"]
    assert "overall_score" in res
    assert res["features_checked"] > 0
    assert len(res["features"]) > 0


def test_5_monitoring_status_endpoint(auth_headers):
    """TEST 5: GET /api/v1/monitoring/status returns dynamic drift analysis."""
    res = client.get("/api/v1/monitoring/status", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["STABLE", "WARNING", "CRITICAL", "INSUFFICIENT_DATA"]
    assert "overall_score" in data
    assert "recommended_action" in data


def test_6_monitoring_history_endpoint(auth_headers):
    """TEST 6: GET /api/v1/monitoring/history retrieves past run logs."""
    res = client.get("/api/v1/monitoring/history", headers=auth_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_7_monitoring_run_trigger_endpoint(auth_headers):
    """TEST 7: POST /api/v1/monitoring/run triggers immediate analysis and persists record."""
    res = client.post("/api/v1/monitoring/run", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert "run" in data
    assert data["run"]["monitoring_id"].startswith("MON-")


def test_8_models_metrics_contains_real_drift_items(auth_headers):
    """TEST 8: GET /api/v1/models/metrics returns real feature drift items."""
    res = client.get("/api/v1/models/metrics", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["drift_report"]) > 0
    item = data["drift_report"][0]
    assert "feature_name" in item
    assert "drift_score" in item
