"""Recommendation Rules Engine (TICKET-403).

Maps customer segment + risk tier to suggested retention actions and ROI estimates.
"""

from pathlib import Path
from typing import Any
import yaml
from business_engine.roi_calculator import calculate_retention_roi

CONFIG_PATH = Path(__file__).parent / "rules_config.yaml"


def _load_rules_config() -> dict[str, Any]:
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def get_recommended_action(
    risk_tier: str,
    churn_prob: float,
    clv: float,
    support_calls_m1: int = 0,
    usage_drop_call_pct: float = 0.0,
    monthly_charges: float = 0.0,
) -> dict[str, Any]:
    """Determine best retention action and return full recommendation payload."""
    config = _load_rules_config()
    actions = config.get("actions", {})

    # Decision Matrix logic
    if support_calls_m1 >= 3 or usage_drop_call_pct > 0.5:
        action_key = "proactive_support"
    elif risk_tier == "High" and monthly_charges > 799:
        action_key = "loyalty_discount"
    elif risk_tier == "High":
        action_key = "contract_incentive"
    elif risk_tier == "Medium":
        action_key = "plan_upgrade_offer"
    else:
        action_key = "standard_survey"

    action_meta = actions.get(action_key, actions.get("standard_survey"))
    
    roi_details = calculate_retention_roi(
        clv=clv,
        churn_prob=churn_prob,
        action_cost=action_meta["cost"],
        expected_save_rate=action_meta["expected_save_rate"],
    )

    return {
        "action_code": action_key,
        "action_name": action_meta["name"],
        "description": action_meta["description"],
        "roi_details": roi_details,
    }
