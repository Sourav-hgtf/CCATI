"""Production Model Performance & Prediction Quality Evaluator Engine (TASK 9).

Evaluates classification performance (Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC, Confusion Matrix) by comparing production predictions against ground-truth customer churn outcomes.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any
import uuid
import numpy as np
import yaml
from backend.app.core.config import settings
from ml_engine.pipelines.evaluation import evaluate_classifier
from ml_engine.registry.model_registry import ModelRegistry


def load_performance_rules_config() -> dict[str, Any]:
    """Load performance degradation rules from centralized YAML configuration."""
    config_path = Path("business_engine/rules_config.yaml")
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data.get("performance_degradation", {})
        except Exception:
            pass
    return {
        "precision_baseline": 0.8392,
        "recall_baseline": 1.0000,
        "f1_baseline": 0.9125,
        "roc_auc_baseline": 0.9432,
        "pr_auc_baseline": 0.8719,
        "warning_drop_pct": 0.05,
        "critical_drop_pct": 0.15,
    }


class PerformanceEvaluator:
    """Production Model Performance Monitoring Engine."""

    def __init__(self, db_path: str = settings.DB_PATH):
        self.db_path = db_path
        self.rules = load_performance_rules_config()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_history_table(self):
        """Create performance_history table if it does not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS performance_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    performance_id TEXT UNIQUE NOT NULL,
                    timestamp TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    status TEXT NOT NULL,
                    precision REAL NOT NULL,
                    recall REAL NOT NULL,
                    f1 REAL NOT NULL,
                    roc_auc REAL NOT NULL,
                    pr_auc REAL NOT NULL,
                    report_json TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def evaluate_production_performance(
        self,
        model_name: str | None = None,
        model_version: str | None = None,
        threshold: float = 0.50,
    ) -> dict[str, Any]:
        """Perform statistical evaluation of production classification performance against ground-truth labels."""
        self._ensure_history_table()

        registry = ModelRegistry()
        try:
            active_info = registry.get_active_model_info()
            m_name = model_name or active_info.get("model_name", "Candidate_RandomForest")
            m_version = model_version or active_info.get("version", "v1788203728")
            baseline_metrics = active_info.get(
                "metrics",
                {
                    "precision": self.rules.get("precision_baseline", 0.8392),
                    "recall": self.rules.get("recall_baseline", 1.0000),
                    "f1": self.rules.get("f1_baseline", 0.9125),
                    "roc_auc": self.rules.get("roc_auc_baseline", 0.9432),
                    "pr_auc": self.rules.get("pr_auc_baseline", 0.8719),
                },
            )
        except Exception:
            m_name = model_name or "Candidate_RandomForest"
            m_version = model_version or "v1788203728"
            baseline_metrics = {
                "precision": self.rules.get("precision_baseline", 0.8392),
                "recall": self.rules.get("recall_baseline", 1.0000),
                "f1": self.rules.get("f1_baseline", 0.9125),
                "roc_auc": self.rules.get("roc_auc_baseline", 0.9432),
                "pr_auc": self.rules.get("pr_auc_baseline", 0.8719),
            }

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    s.customer_id,
                    s.churn_probability,
                    c.churn as actual_churn
                FROM customer_scores s
                JOIN customers c ON s.customer_id = c.customer_id
                WHERE c.churn IS NOT NULL
                """
            )
            rows = cursor.fetchall()

        now_str = datetime.now(timezone.utc).isoformat()
        perf_id = f"PERF-{int(datetime.now(timezone.utc).timestamp() * 1000)}-{uuid.uuid4().hex[:4]}"

        if not rows or len(rows) < 5:
            result = {
                "performance_id": perf_id,
                "status": "UNAVAILABLE",
                "message": "Ground-truth labels unavailable for production performance monitoring.",
                "model_name": m_name,
                "model_version": m_version,
                "threshold": threshold,
                "timestamp": now_str,
                "ground_truth_available": False,
                "sample_count": len(rows) if rows else 0,
                "metrics": None,
                "baseline": baseline_metrics,
                "confusion_matrix": None,
                "alerts": [
                    {
                        "severity": "LOW",
                        "title": "Ground-Truth Labels Missing",
                        "message": "Ground-truth actual customer churn outcomes are not available for production verification.",
                        "timestamp": now_str,
                    }
                ],
                "recommended_action": "Ground-truth labels are required before production performance can be evaluated.",
            }
            return result

        # Extract and sanitize probabilities and labels
        valid_pairs = []
        for r in rows:
            try:
                actual = int(r["actual_churn"])
                prob = float(r["churn_probability"])
                if not np.isnan(prob) and 0.0 <= prob <= 1.0 and actual in (0, 1):
                    valid_pairs.append((actual, prob))
            except (ValueError, TypeError):
                continue

        if len(valid_pairs) < 5:
            result = {
                "performance_id": perf_id,
                "status": "UNAVAILABLE",
                "message": "Insufficient valid ground-truth labels for production performance monitoring.",
                "model_name": m_name,
                "model_version": m_version,
                "threshold": threshold,
                "timestamp": now_str,
                "ground_truth_available": False,
                "sample_count": len(valid_pairs),
                "metrics": None,
                "baseline": baseline_metrics,
                "confusion_matrix": None,
                "alerts": [],
                "recommended_action": "Ground-truth labels are required before production performance can be evaluated.",
            }
            return result

        y_true = np.array([p[0] for p in valid_pairs])
        y_proba = np.array([p[1] for p in valid_pairs])
        y_pred = np.where(y_proba >= threshold, 1, 0)

        clf_metrics = evaluate_classifier(y_true, y_pred, y_proba)
        acc = float(round(np.mean(y_true == y_pred), 4))
        clf_metrics["accuracy"] = acc

        # Calculate actual vs predicted churn rate
        actual_churn_rate = float(round(np.mean(y_true) * 100, 2))
        predicted_churn_rate = float(round(np.mean(y_pred) * 100, 2))
        churn_rate_diff = float(round(predicted_churn_rate - actual_churn_rate, 2))

        # Probability distribution metrics
        prob_stats = {
            "min": float(round(np.min(y_proba), 4)),
            "max": float(round(np.max(y_proba), 4)),
            "mean": float(round(np.mean(y_proba), 4)),
            "median": float(round(np.median(y_proba), 4)),
            "std": float(round(np.std(y_proba), 4)),
        }

        # Calculate performance deltas against baseline
        base_f1 = float(baseline_metrics.get("f1", 0.9125))
        base_roc = float(baseline_metrics.get("roc_auc", 0.9432))

        f1_delta = float(round(clf_metrics["f1"] - base_f1, 4))
        roc_auc_delta = float(round(clf_metrics["roc_auc"] - base_roc, 4))

        crit_drop = self.rules.get("critical_drop_pct", 0.15)
        warn_drop = self.rules.get("warning_drop_pct", 0.05)

        if f1_delta <= -crit_drop or roc_auc_delta <= -crit_drop:
            status = "CRITICAL"
            recommendation = "Significant performance degradation detected! Validate production data and consider model retraining."
        elif f1_delta <= -warn_drop or roc_auc_delta <= -warn_drop:
            status = "WARNING"
            recommendation = "Moderate performance degradation detected compared to baseline. Review recent customer segments."
        else:
            status = "HEALTHY"
            recommendation = "Model performance is within the expected baseline range. Continue regular monitoring schedule."

        deltas = {
            "precision_delta": float(round(clf_metrics["precision"] - float(baseline_metrics.get("precision", 0.8392)), 4)),
            "recall_delta": float(round(clf_metrics["recall"] - float(baseline_metrics.get("recall", 1.0)), 4)),
            "f1_delta": f1_delta,
            "roc_auc_delta": roc_auc_delta,
            "pr_auc_delta": float(round(clf_metrics["pr_auc"] - float(baseline_metrics.get("pr_auc", 0.8719)), 4)),
        }

        result = {
            "performance_id": perf_id,
            "status": status,
            "model_name": m_name,
            "model_version": m_version,
            "threshold": threshold,
            "timestamp": now_str,
            "ground_truth_available": True,
            "sample_count": len(valid_pairs),
            "metrics": clf_metrics,
            "baseline": baseline_metrics,
            "deltas": deltas,
            "confusion_matrix": clf_metrics["confusion_matrix"],
            "churn_rate_analysis": {
                "actual_churn_rate_pct": actual_churn_rate,
                "predicted_churn_rate_pct": predicted_churn_rate,
                "churn_rate_diff_pct": churn_rate_diff,
            },
            "probability_distribution": prob_stats,
            "alerts": [
                {
                    "severity": status,
                    "title": f"Model Performance Health: {status}",
                    "message": recommendation,
                    "timestamp": now_str,
                }
            ],
            "recommended_action": recommendation,
        }

        # Persist run to SQLite history
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO performance_history 
                (performance_id, timestamp, model_name, model_version, status, precision, recall, f1, roc_auc, pr_auc, report_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    perf_id,
                    now_str,
                    m_name,
                    m_version,
                    status,
                    clf_metrics["precision"],
                    clf_metrics["recall"],
                    clf_metrics["f1"],
                    clf_metrics["roc_auc"],
                    clf_metrics["pr_auc"],
                    json.dumps(result),
                ),
            )
            conn.commit()

        return result

    def get_performance_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """Retrieve historical performance evaluation runs."""
        self._ensure_history_table()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM performance_history ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()

        history = []
        for r in rows:
            history.append(
                {
                    "performance_id": r["performance_id"],
                    "timestamp": r["timestamp"],
                    "model_name": r["model_name"],
                    "model_version": r["model_version"],
                    "status": r["status"],
                    "precision": r["precision"],
                    "recall": r["recall"],
                    "f1": r["f1"],
                    "roc_auc": r["roc_auc"],
                    "pr_auc": r["pr_auc"],
                }
            )
        return history
