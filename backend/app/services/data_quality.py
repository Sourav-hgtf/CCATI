"""Production Data Quality & Input Validation Engine (TASK 11).

Provides centralized validation, field-level diagnostics, data quality scoring (0-100),
and dataset quality monitoring prior to ML model inference.
"""

from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any
import numpy as np
import yaml
from backend.app.core.config import settings


def load_data_quality_config() -> dict[str, Any]:
    """Load data quality validation thresholds from centralized YAML configuration."""
    config_path = Path("business_engine/rules_config.yaml")
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data.get("data_quality", {})
        except Exception:
            pass
    return {
        "score_excellent": 90.0,
        "score_good": 75.0,
        "score_warning": 50.0,
        "penalty_critical_error": 25.0,
        "penalty_error": 15.0,
        "penalty_warning": 5.0,
        "penalty_missing_value": 2.0,
        "max_tenure_months": 120,
        "max_monthly_charges": 1000.0,
        "allowed_contract_types": ["Month-to-Month", "Month-to-month", "1-Year", "One year", "2-Year", "Two year"],
        "allowed_plan_tiers": ["Basic", "Standard", "Premium", "Enterprise"],
        "allowed_payment_methods": ["Electronic Check", "Mailed Check", "Bank Transfer", "Credit Card", "UPI", "Net Banking"],
    }


class DataQualityEngine:
    """Central Production Data Quality & Validation Engine."""

    def __init__(self, db_path: str = settings.DB_PATH):
        self.db_path = db_path
        self.config = load_data_quality_config()

    def validate_record(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate an individual customer record against the production feature schema.
        
        Returns structured validation diagnostics, quality score (0-100), and inference eligibility.
        """
        issues: list[dict[str, Any]] = []
        penalties = 0.0

        cid = str(data.get("customer_id", "")).strip() if data.get("customer_id") is not None else ""
        if not cid:
            issues.append({
                "field": "customer_id",
                "issue_type": "missing_required_field",
                "severity": "CRITICAL",
                "message": "Customer ID is required and cannot be null or empty.",
                "value": None,
            })
            penalties += self.config.get("penalty_critical_error", 25.0)

        # 1. Numerical Field Validations
        # Tenure Months
        tenure = data.get("tenure_months")
        if tenure is None or tenure == "":
            issues.append({
                "field": "tenure_months",
                "issue_type": "missing_value",
                "severity": "CRITICAL",
                "message": "Tenure months is required.",
                "value": None,
            })
            penalties += self.config.get("penalty_critical_error", 25.0)
        else:
            try:
                t_val = float(tenure)
                if np.isnan(t_val) or np.isinf(t_val):
                    issues.append({
                        "field": "tenure_months",
                        "issue_type": "invalid_value",
                        "severity": "CRITICAL",
                        "message": "Tenure cannot be NaN or infinite.",
                        "value": str(tenure),
                    })
                    penalties += self.config.get("penalty_critical_error", 25.0)
                elif t_val < 0:
                    issues.append({
                        "field": "tenure_months",
                        "issue_type": "negative_value",
                        "severity": "CRITICAL",
                        "message": f"Tenure cannot be negative (got {t_val}).",
                        "value": t_val,
                    })
                    penalties += self.config.get("penalty_critical_error", 25.0)
                elif t_val > self.config.get("max_tenure_months", 120):
                    issues.append({
                        "field": "tenure_months",
                        "issue_type": "out_of_range",
                        "severity": "WARNING",
                        "message": f"Tenure ({t_val} months) exceeds typical maximum ({self.config.get('max_tenure_months', 120)}).",
                        "value": t_val,
                    })
                    penalties += self.config.get("penalty_warning", 5.0)
            except (ValueError, TypeError):
                issues.append({
                    "field": "tenure_months",
                    "issue_type": "type_mismatch",
                    "severity": "CRITICAL",
                    "message": f"Tenure must be numeric, got '{tenure}'.",
                    "value": str(tenure),
                })
                penalties += self.config.get("penalty_critical_error", 25.0)

        # Monthly Charges
        monthly = data.get("monthly_charges")
        if monthly is None or monthly == "":
            issues.append({
                "field": "monthly_charges",
                "issue_type": "missing_value",
                "severity": "CRITICAL",
                "message": "Monthly charges is required.",
                "value": None,
            })
            penalties += self.config.get("penalty_critical_error", 25.0)
        else:
            try:
                m_val = float(monthly)
                if np.isnan(m_val) or np.isinf(m_val):
                    issues.append({
                        "field": "monthly_charges",
                        "issue_type": "invalid_value",
                        "severity": "CRITICAL",
                        "message": "Monthly charges cannot be NaN or infinite.",
                        "value": str(monthly),
                    })
                    penalties += self.config.get("penalty_critical_error", 25.0)
                elif m_val < 0:
                    issues.append({
                        "field": "monthly_charges",
                        "issue_type": "negative_value",
                        "severity": "CRITICAL",
                        "message": f"Monthly charges cannot be negative (got {m_val}).",
                        "value": m_val,
                    })
                    penalties += self.config.get("penalty_critical_error", 25.0)
                elif m_val > self.config.get("max_monthly_charges", 1000.0):
                    issues.append({
                        "field": "monthly_charges",
                        "issue_type": "out_of_range",
                        "severity": "WARNING",
                        "message": f"Monthly charges ({m_val}) exceeds normal maximum limit.",
                        "value": m_val,
                    })
                    penalties += self.config.get("penalty_warning", 5.0)
            except (ValueError, TypeError):
                issues.append({
                    "field": "monthly_charges",
                    "issue_type": "type_mismatch",
                    "severity": "CRITICAL",
                    "message": f"Monthly charges must be numeric, got '{monthly}'.",
                    "value": str(monthly),
                })
                penalties += self.config.get("penalty_critical_error", 25.0)

        # Total Charges
        total_chg = data.get("total_charges")
        if total_chg is not None and total_chg != "":
            try:
                tot_val = float(total_chg)
                if tot_val < 0:
                    issues.append({
                        "field": "total_charges",
                        "issue_type": "negative_value",
                        "severity": "CRITICAL",
                        "message": f"Total charges cannot be negative (got {tot_val}).",
                        "value": tot_val,
                    })
                    penalties += self.config.get("penalty_critical_error", 25.0)
            except (ValueError, TypeError):
                issues.append({
                    "field": "total_charges",
                    "issue_type": "type_mismatch",
                    "severity": "ERROR",
                    "message": f"Total charges must be numeric, got '{total_chg}'.",
                    "value": str(total_chg),
                })
                penalties += self.config.get("penalty_error", 15.0)

        # Usage / Support Call Fields
        for num_field in ["support_calls_m1", "call_minutes_m1", "call_minutes_m3", "data_gb_m1", "data_gb_m3"]:
            val = data.get(num_field)
            if val is not None and val != "":
                try:
                    f_val = float(val)
                    if f_val < 0:
                        issues.append({
                            "field": num_field,
                            "issue_type": "negative_value",
                            "severity": "ERROR",
                            "message": f"{num_field} cannot be negative (got {f_val}).",
                            "value": f_val,
                        })
                        penalties += self.config.get("penalty_error", 15.0)
                except (ValueError, TypeError):
                    issues.append({
                        "field": num_field,
                        "issue_type": "type_mismatch",
                        "severity": "ERROR",
                        "message": f"{num_field} must be numeric, got '{val}'.",
                        "value": str(val),
                    })
                    penalties += self.config.get("penalty_error", 15.0)

        # 2. Categorical Field Validations
        contract = data.get("contract_type")
        if contract:
            allowed_contracts = [c.lower() for c in self.config.get("allowed_contract_types", [])]
            if str(contract).lower() not in allowed_contracts:
                issues.append({
                    "field": "contract_type",
                    "issue_type": "invalid_category",
                    "severity": "WARNING",
                    "message": f"Unknown contract type '{contract}'.",
                    "value": str(contract),
                })
                penalties += self.config.get("penalty_warning", 5.0)

        plan = data.get("plan_tier")
        if plan:
            allowed_plans = [p.lower() for p in self.config.get("allowed_plan_tiers", [])]
            if str(plan).lower() not in allowed_plans:
                issues.append({
                    "field": "plan_tier",
                    "issue_type": "invalid_category",
                    "severity": "WARNING",
                    "message": f"Unknown plan tier '{plan}'.",
                    "value": str(plan),
                })
                penalties += self.config.get("penalty_warning", 5.0)

        # 3. Cross-Field Consistency Checks
        try:
            if tenure is not None and monthly is not None and total_chg is not None:
                t_val = float(tenure)
                m_val = float(monthly)
                tot_val = float(total_chg)
                if t_val > 12 and tot_val < m_val:
                    issues.append({
                        "field": "total_charges",
                        "issue_type": "inconsistent_combination",
                        "severity": "WARNING",
                        "message": f"Total charges ({tot_val}) is lower than monthly charges ({m_val}) for tenure of {t_val} months.",
                        "value": tot_val,
                    })
                    penalties += self.config.get("penalty_warning", 5.0)
        except Exception:
            pass

        # Calculate final Quality Score (0 to 100)
        score = max(0.0, min(100.0, round(100.0 - penalties, 1)))

        score_exc = self.config.get("score_excellent", 90.0)
        score_gd = self.config.get("score_good", 75.0)
        score_warn = self.config.get("score_warning", 50.0)

        if score >= score_exc:
            status = "EXCELLENT"
        elif score >= score_gd:
            status = "GOOD"
        elif score >= score_warn:
            status = "WARNING"
        else:
            status = "CRITICAL"

        has_critical = any(i["severity"] in ["CRITICAL", "ERROR"] for i in issues)
        can_proceed = not has_critical

        return {
            "customer_id": cid or "UNKNOWN",
            "is_valid": len(issues) == 0,
            "has_critical_errors": has_critical,
            "can_proceed_to_inference": can_proceed,
            "quality_score": score,
            "quality_status": status,
            "issues": issues,
            "issue_count": len(issues),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def audit_database_quality(self) -> dict[str, Any]:
        """Audit data quality of all customer records in the database."""
        from backend.app.db.session import SessionLocal
        from backend.app.db.models.customer import Customer

        session = SessionLocal()
        try:
            cust_models = session.query(Customer).all()
            rows = [
                {col.name: getattr(c, col.name) for col in Customer.__table__.columns}
                for c in cust_models
            ]
        finally:
            session.close()

        total_records = len(rows)
        if total_records == 0:
            return {
                "overall_quality_score": 0.0,
                "quality_status": "CRITICAL",
                "total_records": 0,
                "valid_records": 0,
                "invalid_records": 0,
                "duplicate_count": 0,
                "missing_values_count": 0,
                "field_issues": [],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "alerts": [{"severity": "CRITICAL", "message": "No customer records found in database."}],
            }

        valid_count = 0
        invalid_count = 0
        all_issues: list[dict[str, Any]] = []
        scores = []

        seen_ids = set()
        duplicate_count = 0

        field_issue_agg: dict[str, dict[str, Any]] = {}

        for r in rows:
            cid = r.get("customer_id")
            if cid in seen_ids:
                duplicate_count += 1
            else:
                seen_ids.add(cid)

            rec_res = self.validate_record(r)
            scores.append(rec_res["quality_score"])

            if rec_res["can_proceed_to_inference"]:
                valid_count += 1
            else:
                invalid_count += 1

            for iss in rec_res["issues"]:
                f_name = iss["field"]
                if f_name not in field_issue_agg:
                    field_issue_agg[f_name] = {
                        "field": f_name,
                        "issue_type": iss["issue_type"],
                        "severity": iss["severity"],
                        "affected_count": 0,
                        "sample_message": iss["message"],
                    }
                field_issue_agg[f_name]["affected_count"] += 1

        overall_score = float(round(np.mean(scores), 1)) if scores else 0.0

        score_exc = self.config.get("score_excellent", 90.0)
        score_gd = self.config.get("score_good", 75.0)
        score_warn = self.config.get("score_warning", 50.0)

        if overall_score >= score_exc:
            overall_status = "EXCELLENT"
        elif overall_score >= score_gd:
            overall_status = "GOOD"
        elif overall_score >= score_warn:
            overall_status = "WARNING"
        else:
            overall_status = "CRITICAL"

        now_str = datetime.now(timezone.utc).isoformat()
        alerts = []
        if invalid_count > 0:
            alerts.append({
                "severity": "WARNING" if invalid_count < 20 else "CRITICAL",
                "title": f"Data Quality: {invalid_count} Invalid Records Detected",
                "message": f"{invalid_count} out of {total_records} records failed strict schema validation.",
                "timestamp": now_str,
            })
        else:
            alerts.append({
                "severity": "INFO",
                "title": "Data Quality Optimal",
                "message": f"All {total_records} customer records passed production feature validation.",
                "timestamp": now_str,
            })

        return {
            "overall_quality_score": overall_score,
            "quality_status": overall_status,
            "total_records": total_records,
            "valid_records": valid_count,
            "invalid_records": invalid_count,
            "duplicate_count": duplicate_count,
            "missing_values_count": sum(f["affected_count"] for f in field_issue_agg.values() if "missing" in f["issue_type"]),
            "field_issues": list(field_issue_agg.values()),
            "timestamp": now_str,
            "alerts": alerts,
        }
