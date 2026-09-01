"""Production Model Performance Evaluator and Degradation Detection Engine (TASK 10, TASK 20 PostgreSQL)."""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
import uuid

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
import yaml

from backend.app.core.config import settings
from backend.app.db.models.customer import Customer, CustomerScore
from backend.app.db.models.monitoring import PerformanceHistory
from backend.app.db.session import SessionLocal
from ml_engine.registry.model_registry import ModelRegistry


def load_performance_rules_config() -> dict[str, Any]:
    """Load configurable performance degradation rules and threshold policies."""
    config_path = Path("ml_engine/config/performance_rules.yaml")
    if not config_path.exists():
        return {
            "f1_drop_warning": 0.05,
            "f1_drop_critical": 0.10,
            "roc_auc_drop_warning": 0.05,
            "roc_auc_drop_critical": 0.10,
            "precision_drop_warning": 0.05,
            "precision_drop_critical": 0.10,
            "recall_drop_warning": 0.05,
            "recall_drop_critical": 0.10,
        }
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class PerformanceEvaluator:
    """Production Model Performance Monitoring Engine (PostgreSQL / SQLAlchemy)."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path
        self.rules = load_performance_rules_config()

    def evaluate_production_performance(
        self,
        model_name: str | None = None,
        model_version: str | None = None,
        threshold: float = 0.50,
    ) -> dict[str, Any]:
        """Perform statistical evaluation of production classification performance against ground-truth labels."""
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

        session = SessionLocal()
        try:
            joined_records = (
                session.query(
                    CustomerScore.customer_id,
                    CustomerScore.churn_probability,
                    Customer.churn,
                )
                .join(Customer, CustomerScore.customer_id == Customer.customer_id)
                .filter(Customer.churn.isnot(None))
                .all()
            )
            rows = [
                {
                    "customer_id": r[0],
                    "churn_probability": r[1],
                    "actual_churn": r[2],
                }
                for r in joined_records
            ]
        finally:
            session.close()

        now_str = datetime.now(timezone.utc).isoformat()
        perf_id = f"PERF-{int(datetime.now(timezone.utc).timestamp() * 1000)}-{uuid.uuid4().hex[:4]}"

        if not rows or len(rows) < 5:
            result = {
                "performance_id": perf_id,
                "timestamp": now_str,
                "model_name": m_name,
                "model_version": m_version,
                "status": "INSUFFICIENT_DATA",
                "sample_size": len(rows),
                "metrics": {},
                "baseline_comparison": {},
                "alerts": [
                    {
                        "severity": "WARNING",
                        "title": "Insufficient Labeled Data",
                        "message": f"Only {len(rows)} labeled production records found. Minimum 5 required for evaluation.",
                        "timestamp": now_str,
                    }
                ],
                "recommended_action": "Collect additional ground truth churn labels before running evaluation.",
            }
            return result

        y_true = np.array([int(r["actual_churn"]) for r in rows])
        y_prob = np.array([float(r["churn_probability"]) for r in rows])
        y_pred = (y_prob >= threshold).astype(int)

        # Compute Classification Metrics
        try:
            prec = float(precision_score(y_true, y_pred, zero_division=0))
            rec = float(recall_score(y_true, y_pred, zero_division=0))
            f1 = float(f1_score(y_true, y_pred, zero_division=0))
            acc = float(accuracy_score(y_true, y_pred))
            try:
                roc_auc = float(roc_auc_score(y_true, y_prob))
            except Exception:
                roc_auc = 0.50
            try:
                pr_auc = float(average_precision_score(y_true, y_prob))
            except Exception:
                pr_auc = 0.50
            try:
                lloss = float(log_loss(y_true, y_prob))
            except Exception:
                lloss = 0.0
        except Exception as e:
            prec, rec, f1, acc, roc_auc, pr_auc, lloss = 0.0, 0.0, 0.0, 0.0, 0.50, 0.50, 0.0

        clf_metrics = {
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "accuracy": round(acc, 4),
            "roc_auc": round(roc_auc, 4),
            "pr_auc": round(pr_auc, 4),
            "log_loss": round(lloss, 4),
        }

        # Compare Against Baseline
        base_comp = {}
        alerts = []
        is_critical = False
        is_warning = False

        for metric_name in ["f1", "roc_auc", "precision", "recall", "pr_auc"]:
            current_val = clf_metrics.get(metric_name, 0.0)
            base_val = baseline_metrics.get(metric_name, current_val)
            delta = round(current_val - base_val, 4)
            pct_change = round((delta / base_val * 100) if base_val > 0 else 0.0, 2)

            warn_thresh = self.rules.get(f"{metric_name}_drop_warning", 0.05)
            crit_thresh = self.rules.get(f"{metric_name}_drop_critical", 0.10)

            metric_status = "HEALTHY"
            if delta < -crit_thresh:
                metric_status = "CRITICAL_DROP"
                is_critical = True
                alerts.append(
                    {
                        "severity": "CRITICAL",
                        "title": f"Critical Degradation in {metric_name.upper()}",
                        "message": f"{metric_name.upper()} dropped by {abs(delta):.4f} ({abs(pct_change):.1f}%) from baseline {base_val:.4f} to {current_val:.4f}.",
                        "timestamp": now_str,
                    }
                )
            elif delta < -warn_thresh:
                metric_status = "WARNING_DROP"
                is_warning = True
                alerts.append(
                    {
                        "severity": "WARNING",
                        "title": f"Warning: Degradation in {metric_name.upper()}",
                        "message": f"{metric_name.upper()} dropped by {abs(delta):.4f} ({abs(pct_change):.1f}%) from baseline {base_val:.4f} to {current_val:.4f}.",
                        "timestamp": now_str,
                    }
                )

            base_comp[metric_name] = {
                "current": current_val,
                "baseline": base_val,
                "delta": delta,
                "pct_change": pct_change,
                "status": metric_status,
            }

        # Determine Overall Status
        if is_critical:
            status = "CRITICAL"
            recommendation = (
                "Trigger automated model retraining immediately and inspect root cause data drift in production features."
            )
        elif is_warning:
            status = "DEGRADED"
            recommendation = "Schedule model retraining pipeline and verify feature distribution changes."
        else:
            status = "HEALTHY"
            recommendation = "Model performance meets all SLA benchmarks. Continuous monitoring active."

        result = {
            "performance_id": perf_id,
            "timestamp": now_str,
            "model_name": m_name,
            "model_version": m_version,
            "status": status,
            "sample_size": len(rows),
            "decision_threshold": threshold,
            "metrics": clf_metrics,
            "baseline_comparison": base_comp,
            "alerts": alerts if alerts else [
                {
                    "severity": "INFO",
                    "title": "Model Performance Healthy",
                    "message": f"All classification metrics (F1={clf_metrics['f1']}, ROC-AUC={clf_metrics['roc_auc']}) within SLA targets.",
                    "timestamp": now_str,
                }
            ],
            "recommended_action": recommendation,
        }

        # Persist run to PostgreSQL history
        session = SessionLocal()
        try:
            perf_record = PerformanceHistory(
                performance_id=perf_id,
                timestamp=now_str,
                model_name=m_name,
                model_version=m_version,
                status=status,
                precision=clf_metrics["precision"],
                recall=clf_metrics["recall"],
                f1=clf_metrics["f1"],
                roc_auc=clf_metrics["roc_auc"],
                pr_auc=clf_metrics["pr_auc"],
                report_json=json.dumps(result),
            )
            session.merge(perf_record)
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

        return result

    def get_performance_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """Retrieve historical performance evaluation runs."""
        session = SessionLocal()
        try:
            records = session.query(PerformanceHistory).order_by(
                PerformanceHistory.id.desc()
            ).limit(limit).all()

            history = []
            for r in records:
                history.append(
                    {
                        "performance_id": r.performance_id,
                        "timestamp": r.timestamp,
                        "model_name": r.model_name,
                        "model_version": r.model_version,
                        "status": r.status,
                        "precision": r.precision,
                        "recall": r.recall,
                        "f1": r.f1,
                        "roc_auc": r.roc_auc,
                        "pr_auc": r.pr_auc,
                    }
                )
            return history
        finally:
            session.close()
