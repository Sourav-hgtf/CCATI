"""Data Export Endpoints (TICKET-507, TASK 20 PostgreSQL)."""

import io
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
import pandas as pd
from sqlalchemy.orm import Session

from backend.app.core.audit import log_audit_event
from backend.app.core.rate_limiter import rate_limit_export
from backend.app.core.rbac import UserContext, require_roles
from backend.app.core.security import mask_name, mask_phone
from backend.app.db.models.customer import CustomerScore
from backend.app.db.session import get_db

router = APIRouter()


@router.get("/export/customers", dependencies=[Depends(rate_limit_export)])
def export_at_risk_customers_csv(
    risk_tier: str | None = None,
    plan_tier: str | None = None,
    current_user: UserContext = Depends(require_roles(["RetentionManager", "Admin"])),
    db: Session = Depends(get_db),
):
    """TICKET-507: Export at-risk customer list as CSV (role-gated & logged)."""
    query = db.query(
        CustomerScore.customer_id,
        CustomerScore.name,
        CustomerScore.phone,
        CustomerScore.plan_tier,
        CustomerScore.tenure_months,
        CustomerScore.monthly_charges,
        CustomerScore.churn_probability,
        CustomerScore.risk_tier,
        CustomerScore.priority_score,
    )

    if risk_tier:
        query = query.filter(CustomerScore.risk_tier == risk_tier)
    if plan_tier:
        query = query.filter(CustomerScore.plan_tier == plan_tier)

    records = query.order_by(CustomerScore.priority_score.desc()).all()

    data = [
        {
            "customer_id": r[0],
            "name": r[1],
            "phone": r[2],
            "plan_tier": r[3],
            "tenure_months": r[4],
            "monthly_charges": r[5],
            "churn_probability": r[6],
            "risk_tier": r[7],
            "priority_score": r[8],
        }
        for r in records
    ]

    df = pd.DataFrame(data)
    if df.empty:
        df = pd.DataFrame(columns=[
            "customer_id", "name", "phone", "plan_tier", "tenure_months",
            "monthly_charges", "churn_probability", "risk_tier", "priority_score"
        ])

    # Mask PII in bulk exports by default unless explicit Admin reveal
    if current_user.role != "Admin" and not df.empty:
        df["name"] = df["name"].apply(mask_name)
        df["phone"] = df["phone"].apply(mask_phone)

    stream = io.StringIO()
    df.to_csv(stream, index=False)
    stream.seek(0)

    log_audit_event(
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="EXPORT_CUSTOMERS_CSV",
        target_resource="customers_csv_export",
        details=f"Exported {len(df)} customer records (Filters: risk_tier={risk_tier}, plan_tier={plan_tier})",
    )

    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=at_risk_customers.csv"
    return response
