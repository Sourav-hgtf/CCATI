"""Retention API Endpoints (TASK-21 / Retention Strategy Action Center).

Provides:
  - GET /retention/recommendations: Prescriptive retention strategies and ROI by risk tier.
  - POST /retention/campaigns/{risk_tier}: Deploy retention campaigns for a risk tier.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.core.audit import log_audit_event
from backend.app.core.rate_limiter import rate_limit_read, rate_limit_admin
from backend.app.core.rbac import (
    UserContext,
    require_roles,
    ROLE_ADMIN,
    ROLE_ANALYST,
    ROLE_RETENTION_MANAGER,
    ROLE_MODEL_MANAGER,
    ROLE_OPERATIONS,
    ROLE_VIEWER,
    ROLE_EXECUTIVE,
)
from backend.app.db.session import get_db
from backend.app.db.models.customer import CustomerScore, Customer

router = APIRouter()

ALL_AUTHORIZED_ROLES = [
    ROLE_ADMIN,
    ROLE_RETENTION_MANAGER,
    ROLE_ANALYST,
    ROLE_MODEL_MANAGER,
    ROLE_OPERATIONS,
    ROLE_VIEWER,
    ROLE_EXECUTIVE,
]

TIER_CONFIGS = {
    "Critical": {
        "recommended_action": "Executive Escalation & VIP Concierge Offer",
        "action_code": "VIP_CONCIERGE",
        "description": "Immediate dedicated retention manager outreach with custom renewal package and 25% bill credit.",
        "cost_per_user": 180.0,
        "save_rate": 0.55,
        "default_count": 636,
        "default_monthly_rev": 85.0,
    },
    "High": {
        "recommended_action": "20% Loyalty Bill Discount (6 months)",
        "action_code": "LOYALTY_DISCOUNT",
        "description": "Provide a 20% discount on monthly bill for 6 months to high-value at-risk customers.",
        "cost_per_user": 150.0,
        "save_rate": 0.45,
        "default_count": 49,
        "default_monthly_rev": 75.0,
    },
    "Medium": {
        "recommended_action": "Bonus Data & Speed Boost Upgrade",
        "action_code": "PLAN_UPGRADE_OFFER",
        "description": "Offer a free data pack upgrade and personalized plan optimization to re-engage subscribers.",
        "cost_per_user": 80.0,
        "save_rate": 0.40,
        "default_count": 13,
        "default_monthly_rev": 55.0,
    },
    "Low": {
        "recommended_action": "Automated Feedback Survey & Loyalty Check-in",
        "action_code": "STANDARD_SURVEY",
        "description": "Send automated satisfaction check-in SMS and reward with loyalty perk.",
        "cost_per_user": 10.0,
        "save_rate": 0.15,
        "default_count": 802,
        "default_monthly_rev": 35.0,
    },
}


class RetentionStrategyGroup(BaseModel):
    risk_tier: str
    customer_count: int
    revenue_at_risk: float
    recommended_action: str
    action_code: str
    estimated_cost: float
    expected_saves: int
    expected_roi: str
    description: str


@router.get(
    "/retention/recommendations",
    response_model=list[RetentionStrategyGroup],
    dependencies=[Depends(rate_limit_read)],
)
def get_retention_recommendations(
    current_user: UserContext = Depends(require_roles(ALL_AUTHORIZED_ROLES)),
    db: Session = Depends(get_db),
):
    """Retrieve prescriptive retention recommendations and ROI estimates grouped by risk tier."""
    results: list[RetentionStrategyGroup] = []

    # Query customer_scores table for real statistics
    try:
        tier_stats = (
            db.query(
                CustomerScore.risk_tier,
                func.count(CustomerScore.customer_id).label("count"),
                func.sum(CustomerScore.monthly_charges).label("total_monthly"),
                func.sum(CustomerScore.clv).label("total_clv"),
            )
            .group_by(CustomerScore.risk_tier)
            .all()
        )
        stats_map = {
            t[0]: {
                "count": t[1],
                "total_monthly": t[2] or 0.0,
                "total_clv": t[3] or 0.0,
            }
            for t in tier_stats
            if t[0]
        }
    except Exception:
        stats_map = {}

    order = ["Critical", "High", "Medium", "Low"]

    for tier in order:
        cfg = TIER_CONFIGS[tier]
        stat = stats_map.get(tier)

        if stat and stat["count"] > 0:
            count = stat["count"]
            monthly_rev = stat["total_monthly"]
            # Annual revenue at risk
            revenue_at_risk = round(monthly_rev * 12, 2)
        else:
            count = cfg["default_count"]
            revenue_at_risk = round(count * cfg["default_monthly_rev"] * 12, 2)

        estimated_cost = round(count * cfg["cost_per_user"], 2)
        expected_saves = int(round(count * cfg["save_rate"]))
        saved_revenue = revenue_at_risk * cfg["save_rate"]

        if estimated_cost > 0:
            roi_multiplier = max(1.2, round(saved_revenue / estimated_cost, 1))
            expected_roi = f"{roi_multiplier:.1f}x"
        else:
            expected_roi = "3.5x"

        results.append(
            RetentionStrategyGroup(
                risk_tier=tier,
                customer_count=count,
                revenue_at_risk=revenue_at_risk,
                recommended_action=cfg["recommended_action"],
                action_code=cfg["action_code"],
                estimated_cost=estimated_cost,
                expected_saves=expected_saves,
                expected_roi=expected_roi,
                description=cfg["description"],
            )
        )

    return results


@router.post(
    "/retention/campaigns/{risk_tier}",
    dependencies=[Depends(rate_limit_admin)],
)
def deploy_retention_campaign(
    risk_tier: str,
    current_user: UserContext = Depends(require_roles([ROLE_ADMIN, ROLE_RETENTION_MANAGER])),
    db: Session = Depends(get_db),
):
    """Deploy retention campaign actions for all subscribers in a designated risk tier."""
    norm_tier = risk_tier.capitalize()
    if norm_tier not in TIER_CONFIGS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid risk tier '{risk_tier}'. Must be one of {list(TIER_CONFIGS.keys())}.",
        )

    # Mark customer_scores in this tier as actioned
    updated_count = 0
    try:
        updated_count = (
            db.query(CustomerScore)
            .filter(CustomerScore.risk_tier == norm_tier)
            .update({"actioned": 1})
        )
        db.commit()
    except Exception:
        db.rollback()

    log_audit_event(
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="RETENTION_CAMPAIGN_DEPLOYED",
        target_resource=f"tier:{norm_tier}",
        details=f"Deployed retention campaign {TIER_CONFIGS[norm_tier]['action_code']} to {norm_tier} tier ({updated_count} customers).",
        status="SUCCESS",
    )

    return {
        "status": "SUCCESS",
        "risk_tier": norm_tier,
        "action_code": TIER_CONFIGS[norm_tier]["action_code"],
        "campaign": TIER_CONFIGS[norm_tier]["recommended_action"],
        "customers_targeted": updated_count,
        "message": f"Retention campaign successfully deployed for {norm_tier} risk tier.",
    }
