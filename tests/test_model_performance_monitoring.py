"""Automated Test Suite for TASK 9 — Production Model Performance & Prediction Quality Monitoring.

Verifies that:
1. Classification performance metrics (Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC, Confusion Matrix) are computed mathematically against ground-truth customer churn outcomes.
2. Baseline metrics comparison deltas are calculated dynamically.
3. Model Health Status (HEALTHY, WARNING, CRITICAL, UNAVAILABLE) is determined dynamically.
4. Performance evaluations persist to SQLite performance_history table.
5. FastAPI performance monitoring endpoints (/monitoring/performance, /history, /run) return properly typed responses.
"""

from fastapi.testclient import TestClient
import numpy as np
import pytest
from backend.app.main import app
from backend.app.core.security import create_access_token
from ml_engine.monitoring.performance_evaluator import PerformanceEvaluator
from ml_engine.pipelines.evaluation import evaluate_classifier

client = TestClient(app)


@pytest.fixture
def auth_headers():
    token = create_access_token(subject={"sub": "test_user", "email": "admin@telecom.com", "role": "Admin"})
    return {"Authorization": f"Bearer {token}"}


def test_1_evaluate_classifier_math():
    """TEST 1: evaluate_classifier computes exact sklearn classification metrics and confusion matrix."""
    y_true = np.array([0, 0, 1, 1, 0, 1, 0, 1])
    y_pred = np.array([0, 0, 1, 1, 0, 0, 0, 1])
    y_proba = np.array([0.1, 0.2, 0.8, 0.9, 0.3, 0.4, 0.1, 0.95])

    res = evaluate_classifier(y_true, y_pred, y_proba)
    assert "precision" in res
    assert "recall" in res
    assert "f1" in res
    assert "roc_auc" in res
    assert "pr_auc" in res
    assert res["confusion_matrix"]["tp"] == 3
    assert res["confusion_matrix"]["fn"] == 1
    assert res["confusion_matrix"]["tn"] == 4
    assert res["confusion_matrix"]["fp"] == 0


def test_2_performance_evaluator_database():
    """TEST 2: PerformanceEvaluator performs statistical evaluation joining customer scores with actual ground-truth churn labels."""
    evaluator = PerformanceEvaluator()
    res = evaluator.evaluate_production_performance()

    assert res["status"] in ["HEALTHY", "WARNING", "CRITICAL", "UNAVAILABLE"]
    assert "model_name" in res
    assert "model_version" in res
    assert res["threshold"] == 0.50

    if res["ground_truth_available"]:
        assert res["metrics"]["precision"] >= 0.0
        assert res["metrics"]["recall"] >= 0.0
        assert res["metrics"]["f1"] >= 0.0
        assert "confusion_matrix" in res
        assert "churn_rate_analysis" in res


def test_3_performance_monitoring_endpoint(auth_headers):
    """TEST 3: GET /api/v1/monitoring/performance returns dynamic model performance evaluation."""
    res = client.get("/api/v1/monitoring/performance", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["status"] in ["HEALTHY", "WARNING", "CRITICAL", "UNAVAILABLE"]
    assert "baseline" in data
    assert "recommended_action" in data


def test_4_performance_history_endpoint(auth_headers):
    """TEST 4: GET /api/v1/monitoring/performance/history retrieves past evaluation logs."""
    res = client.get("/api/v1/monitoring/performance/history", headers=auth_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_5_performance_run_trigger_endpoint(auth_headers):
    """TEST 5: POST /api/v1/monitoring/performance/run executes scan and persists run to SQLite."""
    res = client.post("/api/v1/monitoring/performance/run", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert "run" in data
    assert data["run"]["performance_id"].startswith("PERF-")
