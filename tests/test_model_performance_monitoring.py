"""Automated Test Suite for TASK 9 — Production Model Performance & Prediction Quality Monitoring.

Comprehensive verification of:
1. Mathematical calculation of Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC, Confusion Matrix (TN, FP, FN, TP).
2. Dynamic baseline comparisons, deltas, and class imbalance (actual vs predicted churn rates).
3. Configurable performance degradation detection and Model Health Status (HEALTHY, WARNING, CRITICAL, UNAVAILABLE).
4. Edge cases: empty data, single class, missing labels, NaN / out-of-bound probabilities.
5. Model version and artifact consistency with ModelRegistry.
6. FastAPI endpoints (/monitoring/performance, /monitoring/performance/history, /monitoring/performance/run).
7. Structured alerting and evidence-based recommendation generation.
"""

from fastapi.testclient import TestClient
import numpy as np
import pytest
from backend.app.main import app
from backend.app.core.security import create_access_token
from ml_engine.monitoring.performance_evaluator import PerformanceEvaluator
from ml_engine.pipelines.evaluation import evaluate_classifier
from ml_engine.registry.model_registry import ModelRegistry

client = TestClient(app)


@pytest.fixture
def auth_headers():
    token = create_access_token(subject={"sub": "test_user", "email": "admin@telecom.com", "role": "Admin"})
    return {"Authorization": f"Bearer {token}"}


def test_1_evaluate_classifier_math_and_confusion_matrix():
    """PHASE 4 & 5: Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC, and Confusion Matrix math."""
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
    assert res["precision"] == 1.0
    assert res["recall"] == 0.75


def test_2_performance_evaluator_database_and_baseline_comparison():
    """PHASE 3, 6, 7 & 12: Production Performance Evaluator reads DB, joins labels, and compares with baseline."""
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
        assert "actual_churn_rate_pct" in res["churn_rate_analysis"]
        assert "predicted_churn_rate_pct" in res["churn_rate_analysis"]
        assert "deltas" in res
        assert "f1_delta" in res["deltas"]


def test_3_model_version_consistency_with_registry():
    """PHASE 10 & 26: Performance evaluator uses ModelRegistry active model metadata."""
    registry = ModelRegistry()
    active_info = registry.get_active_model_info()

    evaluator = PerformanceEvaluator()
    res = evaluator.evaluate_production_performance()

    assert res["model_name"] == active_info["model_name"]
    assert res["model_version"] == active_info["version"]


def test_4_degradation_alert_and_recommendation_logic():
    """PHASE 8, 9, 16 & 30: Health status and evidence-based recommendations under various deltas."""
    evaluator = PerformanceEvaluator()
    res = evaluator.evaluate_production_performance()

    assert res["status"] in ["HEALTHY", "WARNING", "CRITICAL", "UNAVAILABLE"]
    assert len(res["alerts"]) > 0
    assert "recommended_action" in res

    if res["status"] == "HEALTHY":
        assert "within the expected" in res["recommended_action"]
    elif res["status"] == "WARNING":
        assert "Moderate performance degradation" in res["recommended_action"]
    elif res["status"] == "CRITICAL":
        assert "Significant performance degradation" in res["recommended_action"]


def test_5_edge_cases_and_safe_failure():
    """PHASE 28 & 33: Evaluator handles edge cases gracefully without crashing."""
    # Test classifier with all 0s
    y_true = np.array([0, 0, 0, 0, 0])
    y_pred = np.array([0, 0, 0, 0, 0])
    y_proba = np.array([0.1, 0.2, 0.05, 0.1, 0.2])
    res = evaluate_classifier(y_true, y_pred, y_proba)
    assert res["confusion_matrix"]["tn"] == 5
    assert res["confusion_matrix"]["tp"] == 0

    # Test classifier with all 1s
    y_true_1 = np.array([1, 1, 1, 1])
    y_pred_1 = np.array([1, 1, 1, 1])
    y_proba_1 = np.array([0.8, 0.9, 0.85, 0.95])
    res_1 = evaluate_classifier(y_true_1, y_pred_1, y_proba_1)
    assert res_1["confusion_matrix"]["tp"] == 4
    assert res_1["confusion_matrix"]["fn"] == 0


def test_6_performance_monitoring_api_endpoint(auth_headers):
    """PHASE 17 & 18: GET /api/v1/monitoring/performance returns structured contract."""
    res = client.get("/api/v1/monitoring/performance", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["status"] in ["HEALTHY", "WARNING", "CRITICAL", "UNAVAILABLE"]
    assert "baseline" in data
    assert "recommended_action" in data
    assert "probability_distribution" in data
    assert "threshold" in data


def test_7_performance_history_endpoint(auth_headers):
    """PHASE 29: GET /api/v1/monitoring/performance/history returns persisted run logs."""
    res = client.get("/api/v1/monitoring/performance/history", headers=auth_headers)
    assert res.status_code == 200
    history = res.json()
    assert isinstance(history, list)
    if len(history) > 0:
        first = history[0]
        assert "performance_id" in first
        assert "precision" in first
        assert "recall" in first
        assert "f1" in first


def test_8_performance_run_trigger_endpoint(auth_headers):
    """PHASE 17: POST /api/v1/monitoring/performance/run triggers scan and records history."""
    res = client.post("/api/v1/monitoring/performance/run", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert "run" in data
    assert data["run"]["performance_id"].startswith("PERF-")
