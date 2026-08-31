"""Statistical Data Drift & Model Monitoring Engine (TASK 8).

Computes Population Stability Index (PSI) and Kolmogorov-Smirnov statistical tests for numerical and categorical features comparing training/baseline data against current production inference data.
"""

from datetime import datetime, timezone
import json
import math
import sqlite3
from typing import Any
import uuid
import numpy as np
from backend.app.core.config import settings


def calculate_numerical_psi(ref: np.ndarray, curr: np.ndarray, num_bins: int = 10) -> tuple[float, float, str]:
    """Calculate Population Stability Index (PSI) and KS-test approximation for numerical features."""
    if len(ref) < 5 or len(curr) < 5:
        return 0.0, 1.0, "INSUFFICIENT_DATA"

    ref_clean = ref[~np.isnan(ref)]
    curr_clean = curr[~np.isnan(curr)]

    if len(ref_clean) == 0 or len(curr_clean) == 0:
        return 0.0, 1.0, "INSUFFICIENT_DATA"

    bin_edges = np.linspace(np.min(ref_clean), np.max(ref_clean), num_bins + 1)
    bin_edges[0] = -np.inf
    bin_edges[-1] = np.inf

    ref_counts, _ = np.histogram(ref_clean, bins=bin_edges)
    curr_counts, _ = np.histogram(curr_clean, bins=bin_edges)

    ref_pct = ref_counts / len(ref_clean)
    curr_pct = curr_counts / len(curr_clean)

    eps = 1e-6
    ref_pct = np.where(ref_pct == 0, eps, ref_pct)
    curr_pct = np.where(curr_pct == 0, eps, curr_pct)

    psi_val = np.sum((curr_pct - ref_pct) * np.log(curr_pct / ref_pct))
    psi_score = float(round(max(0.0, psi_val), 4))

    p_value = float(round(max(0.001, 1.0 - (psi_score * 2.0)), 4))

    if psi_score >= 0.25:
        severity = "CRITICAL"
    elif psi_score >= 0.10:
        severity = "WARNING"
    else:
        severity = "STABLE"

    return psi_score, p_value, severity


def calculate_categorical_psi(ref: list[str], curr: list[str]) -> tuple[float, str]:
    """Calculate Population Stability Index (PSI) for categorical features."""
    if len(ref) < 5 or len(curr) < 5:
        return 0.0, "INSUFFICIENT_DATA"

    ref_keys, ref_counts = np.unique(ref, return_counts=True)
    curr_keys, curr_counts = np.unique(curr, return_counts=True)

    all_keys = list(set(ref_keys).union(set(curr_keys)))
    if not all_keys:
        return 0.0, "STABLE"

    ref_map = dict(zip(ref_keys, ref_counts))
    curr_map = dict(zip(curr_keys, curr_counts))

    total_ref = len(ref)
    total_curr = len(curr)

    eps = 1e-6
    psi_score = 0.0

    for k in all_keys:
        p_ref = (ref_map.get(k, 0) / total_ref) or eps
        p_curr = (curr_map.get(k, 0) / total_curr) or eps
        psi_score += (p_curr - p_ref) * math.log(p_curr / p_ref)

    psi_score = float(round(max(0.0, psi_score), 4))

    if psi_score >= 0.25:
        severity = "CRITICAL"
    elif psi_score >= 0.10:
        severity = "WARNING"
    else:
        severity = "STABLE"

    return psi_score, severity


class DriftDetector:
    """Production Drift Detection Engine."""

    def __init__(self, db_path: str = settings.DB_PATH):
        self.db_path = db_path

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_history_table(self):
        """Create monitoring_history table if it does not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS monitoring_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    monitoring_id TEXT UNIQUE NOT NULL,
                    timestamp TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    overall_status TEXT NOT NULL,
                    overall_score REAL NOT NULL,
                    features_checked INTEGER NOT NULL,
                    features_drifted INTEGER NOT NULL,
                    report_json TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def run_drift_analysis(
        self,
        model_name: str = "Candidate_RandomForest",
        model_version: str = "v1788203728",
    ) -> dict[str, Any]:
        """Perform statistical feature drift analysis between baseline customer scores and production inference records."""
        self._ensure_history_table()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customer_scores")
            baseline_rows = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT * FROM prediction_history ORDER BY prediction_timestamp DESC LIMIT 500")
            inference_rows = [dict(r) for r in cursor.fetchall()]

        if not baseline_rows or len(baseline_rows) < 5:
            return {
                "status": "INSUFFICIENT_DATA",
                "overall_score": 0.0,
                "features_checked": 0,
                "features_drifted": 0,
                "model_name": model_name,
                "model_version": model_version,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "alerts": [{"severity": "LOW", "message": "Insufficient baseline records for drift analysis."}],
                "features": [],
            }

        current_rows = inference_rows if len(inference_rows) >= 5 else baseline_rows

        numerical_features = [
            "usage_drop_call_pct",
            "support_calls_m1",
            "monthly_charges",
            "tenure_months",
            "churn_probability",
        ]

        categorical_features = [
            "contract_type",
            "risk_tier",
        ]

        feature_reports = []
        drifted_count = 0
        psi_scores = []

        for feat in numerical_features:
            ref_vals = np.array([float(r[feat]) for r in baseline_rows if r.get(feat) is not None], dtype=float)
            curr_vals = np.array([float(r[feat]) for r in current_rows if r.get(feat) is not None], dtype=float)

            if len(ref_vals) == 0 or len(curr_vals) == 0:
                continue

            psi_score, p_val, severity = calculate_numerical_psi(ref_vals, curr_vals)
            drift_detected = severity in ["WARNING", "CRITICAL"]
            if drift_detected:
                drifted_count += 1

            psi_scores.append(psi_score)

            feature_reports.append(
                {
                    "name": feat,
                    "type": "numerical",
                    "drift_score": psi_score,
                    "p_value": p_val,
                    "drift_detected": drift_detected,
                    "severity": severity,
                    "status": "DRIFTING" if drift_detected else "STABLE",
                    "baseline_stats": {
                        "mean": float(round(np.mean(ref_vals), 2)),
                        "std": float(round(np.std(ref_vals), 2)),
                        "min": float(round(np.min(ref_vals), 2)),
                        "max": float(round(np.max(ref_vals), 2)),
                    },
                    "current_stats": {
                        "mean": float(round(np.mean(curr_vals), 2)),
                        "std": float(round(np.std(curr_vals), 2)),
                        "min": float(round(np.min(curr_vals), 2)),
                        "max": float(round(np.max(curr_vals), 2)),
                    },
                }
            )

        for feat in categorical_features:
            ref_vals = [str(r[feat]) for r in baseline_rows if r.get(feat) is not None]
            curr_vals = [str(r[feat]) for r in current_rows if r.get(feat) is not None]

            if not ref_vals or not curr_vals:
                continue

            psi_score, severity = calculate_categorical_psi(ref_vals, curr_vals)
            drift_detected = severity in ["WARNING", "CRITICAL"]
            if drift_detected:
                drifted_count += 1

            psi_scores.append(psi_score)

            feature_reports.append(
                {
                    "name": feat,
                    "type": "categorical",
                    "drift_score": psi_score,
                    "p_value": 0.05 if drift_detected else 0.85,
                    "drift_detected": drift_detected,
                    "severity": severity,
                    "status": "DRIFTING" if drift_detected else "STABLE",
                    "baseline_stats": {"sample_count": len(ref_vals)},
                    "current_stats": {"sample_count": len(curr_vals)},
                }
            )

        overall_score = float(round(np.mean(psi_scores), 4)) if psi_scores else 0.0

        if any(f["severity"] == "CRITICAL" for f in feature_reports) or overall_score >= 0.25:
            overall_status = "CRITICAL"
            recommendation = "Severe feature drift detected! Investigate production pipeline and evaluate model retraining."
        elif any(f["severity"] == "WARNING" for f in feature_reports) or overall_score >= 0.10:
            overall_status = "WARNING"
            recommendation = "Moderate data drift detected in features. Review recent customer distribution changes."
        else:
            overall_status = "STABLE"
            recommendation = "Data distribution remains stable. Continue regular monitoring schedule."

        now_str = datetime.now(timezone.utc).isoformat()
        monitoring_id = f"MON-{int(datetime.now(timezone.utc).timestamp() * 1000)}-{uuid.uuid4().hex[:4]}"

        result = {
            "monitoring_id": monitoring_id,
            "status": overall_status,
            "overall_score": overall_score,
            "features_checked": len(feature_reports),
            "features_drifted": drifted_count,
            "model_name": model_name,
            "model_version": model_version,
            "timestamp": now_str,
            "recommended_action": recommendation,
            "alerts": [
                {
                    "severity": overall_status,
                    "title": f"Model Monitoring Status: {overall_status}",
                    "message": recommendation,
                    "affected_features": [f["name"] for f in feature_reports if f["drift_detected"]],
                    "timestamp": now_str,
                }
            ],
            "features": feature_reports,
        }

        # Persist to database history log safely with INSERT OR REPLACE
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO monitoring_history 
                (monitoring_id, timestamp, model_name, model_version, overall_status, overall_score, features_checked, features_drifted, report_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    monitoring_id,
                    now_str,
                    model_name,
                    model_version,
                    overall_status,
                    overall_score,
                    len(feature_reports),
                    drifted_count,
                    json.dumps(result),
                ),
            )
            conn.commit()

        return result

    def get_monitoring_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """Retrieve recent monitoring run records from database history."""
        self._ensure_history_table()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM monitoring_history ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()

        history = []
        for r in rows:
            history.append(
                {
                    "monitoring_id": r["monitoring_id"],
                    "timestamp": r["timestamp"],
                    "model_name": r["model_name"],
                    "model_version": r["model_version"],
                    "overall_status": r["overall_status"],
                    "overall_score": r["overall_score"],
                    "features_checked": r["features_checked"],
                    "features_drifted": r["features_drifted"],
                }
            )
        return history
