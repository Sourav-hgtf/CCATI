"""Data Export Endpoints (TICKET-507)."""

import io
import sqlite3
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
import pandas as pd
from backend.app.core.audit import log_audit_event
from backend.app.core.config import settings
from backend.app.core.rbac import UserContext, require_roles
from backend.app.core.security import mask_name, mask_phone

router = APIRouter()


@router.get("/export/customers")
def export_at_risk_customers_csv(
    risk_tier: str | None = None,
    plan_tier: str | None = None,
    current_user: UserContext = Depends(require_roles(["RetentionManager", "Admin"])),
):
    """TICKET-507: Export at-risk customer list as CSV (role-gated & logged)."""
    conn = sqlite3.connect(settings.DB_PATH)

    sql = "SELECT customer_id, name, phone, plan_tier, tenure_months, monthly_charges, churn_probability, risk_tier, priority_score FROM customer_scores WHERE 1=1"
    params = []
    if risk_tier:
        sql += " AND risk_tier = ?"
        params.append(risk_tier)
    if plan_tier:
        sql += " AND plan_tier = ?"
        params.append(plan_tier)

    sql += " ORDER BY priority_score DESC"

    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()

    # Mask PII in bulk exports by default unless explicit Admin reveal
    if current_user.role != "Admin":
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
