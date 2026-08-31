"""Customer Endpoints (TICKET-502, TICKET-503, TICKET-603, TICKET-704)."""

from datetime import datetime, timezone
import json
import math
import sqlite3
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from backend.app.core.audit import log_audit_event
from backend.app.core.config import settings
from backend.app.core.rbac import UserContext, get_current_user, require_roles
from backend.app.core.security import mask_email, mask_name, mask_phone
from backend.app.schemas.customer import (
    CustomerDetailResponse,
    CustomerListItem,
    CustomerPaginatedResponse,
)
from backend.app.services.scoring_service import run_full_scoring_job

router = APIRouter()


def _ensure_data_seeded():
    """Ensure scored customer database is populated."""
    conn = sqlite3.connect(settings.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customer_scores'")
    table_exists = cursor.fetchone()
    conn.close()

    if not table_exists:
        print("Database table customer_scores missing. Running initial batch scoring...")
        run_full_scoring_job(force_ingestion=True)


@router.get("/customers", response_model=CustomerPaginatedResponse)
def get_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    risk_tier: str | None = None,
    plan_tier: str | None = None,
    segment_id: int | None = None,
    search: str | None = None,
    sort_by: str = Query("priority_score", pattern="^(priority_score|churn_probability|tenure_months|monthly_charges)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: UserContext = Depends(require_roles(["RetentionManager", "Analyst", "Admin", "Executive"])),
):
    """TICKET-502: GET /api/v1/customers (paginated, filterable, sortable)."""
    _ensure_data_seeded()
    conn = sqlite3.connect(settings.DB_PATH)
    cursor = conn.cursor()

    query_parts = ["FROM customer_scores WHERE 1=1"]
    params = []

    if risk_tier:
        query_parts.append("AND risk_tier = ?")
        params.append(risk_tier)
    if plan_tier:
        query_parts.append("AND plan_tier = ?")
        params.append(plan_tier)
    if segment_id is not None:
        query_parts.append("AND cluster_id = ?")
        params.append(segment_id)
    if search:
        query_parts.append("AND (customer_id LIKE ? OR name LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])

    where_clause = " ".join(query_parts)

    # Count total
    count_sql = f"SELECT COUNT(*) {where_clause}"
    cursor.execute(count_sql, params)
    total_records = cursor.fetchone()[0]

    # Select paginated records
    offset = (page - 1) * page_size
    select_sql = f"""
        SELECT customer_id, name, phone, plan_tier, tenure_months, monthly_charges,
               churn_probability, risk_tier, priority_score, usage_drop_call_pct,
               support_calls_m1, recommendation_json, cluster_id
        {where_clause}
        ORDER BY {sort_by} {sort_order.upper()}
        LIMIT ? OFFSET ?
    """
    params.extend([page_size, offset])
    cursor.execute(select_sql, params)
    rows = cursor.fetchall()
    conn.close()

    items = []
    for r in rows:
        rec_data = json.loads(r[11]) if r[11] else {}
        items.append(
            CustomerListItem(
                customer_id=r[0],
                name=mask_name(r[1]),  # Mask PII by default in list views
                phone=mask_phone(r[2]),
                plan_tier=r[3],
                tenure_months=r[4],
                monthly_charges=r[5],
                churn_probability=r[6],
                risk_tier=r[7],
                priority_score=r[8],
                usage_drop_call_pct=r[9],
                support_calls_m1=r[10],
                recommended_action=rec_data.get("action_name", "Standard Engagement"),
                segment_id=r[12],
            )
        )

    total_pages = math.ceil(total_records / page_size) if total_records > 0 else 1

    return CustomerPaginatedResponse(
        total=total_records,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=items,
    )


@router.get("/customers/{customer_id}", response_model=CustomerDetailResponse)
def get_customer_detail(
    customer_id: str,
    reveal_pii: bool = False,
    current_user: UserContext = Depends(require_roles(["RetentionManager", "Analyst", "Admin", "Executive"])),
):
    """TICKET-503: GET /api/v1/customers/{id} (full customer detail payload)."""
    _ensure_data_seeded()
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM customer_scores WHERE customer_id = ?", (customer_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Customer record not found")

    # Fetch call logs for history
    cursor.execute("SELECT call_reason, sentiment, resolved, duration_sec FROM call_logs WHERE customer_id = ?", (customer_id,))
    call_rows = cursor.fetchall()
    call_logs = [dict(c) for c in call_rows]
    conn.close()

    shap_features = json.loads(row["shap_json"]) if row["shap_json"] else []
    rec_payload = json.loads(row["recommendation_json"]) if row["recommendation_json"] else {}
    rec_payload["actioned"] = bool(row["actioned"])
    rec_payload["actioned_at"] = row["actioned_at"]

    # Check PII permissions
    if reveal_pii and current_user.role not in ["RetentionManager", "Admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Unmasking PII is restricted to RetentionManager and Admin roles. Current role: '{current_user.role}'",
        )

    should_mask = not reveal_pii

    if reveal_pii:
        log_audit_event(
            actor_email=current_user.email,
            actor_role=current_user.role,
            action="PII_REVEAL",
            target_resource=f"customer:{customer_id}",
            details="User accessed unmasked customer PII details",
        )

    # Usage trend series
    usage_history = [
        {"month": "M-3", "call_minutes": round(row["usage_drop_call_pct"] * 100, 1), "support_calls": max(0, row["support_calls_m1"] - 2)},
        {"month": "M-2", "call_minutes": round(row["usage_drop_call_pct"] * 50, 1), "support_calls": max(0, row["support_calls_m1"] - 1)},
        {"month": "M-1", "call_minutes": row["usage_drop_call_pct"], "support_calls": row["support_calls_m1"]},
    ]

    return CustomerDetailResponse(
        customer_id=row["customer_id"],
        name=row["name"] if not should_mask else mask_name(row["name"]),
        phone=row["phone"] if not should_mask else mask_phone(row["phone"]),
        email=row["email"] if not should_mask else mask_email(row["email"]),
        is_pii_revealed=not should_mask,
        plan_tier=row["plan_tier"],
        contract_type=row["contract_type"],
        payment_method=row["payment_method"],
        tenure_months=row["tenure_months"],
        monthly_charges=row["monthly_charges"],
        total_charges=row["total_charges"],
        churn_probability=row["churn_probability"],
        risk_tier=row["risk_tier"],
        priority_score=row["priority_score"],
        clv=row["clv"],
        usage_history=usage_history,
        top_shap_features=shap_features,
        recommendation=rec_payload,
        call_log_history=call_logs,
        segment_id=row["cluster_id"],
    )


@router.post("/customers/{customer_id}/action")
def mark_customer_actioned(
    customer_id: str,
    current_user: UserContext = Depends(require_roles(["RetentionManager", "Admin"])),
):
    """TICKET-704: Mark retention recommendation as actioned."""
    conn = sqlite3.connect(settings.DB_PATH)
    cursor = conn.cursor()

    now_iso = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        "UPDATE customer_scores SET actioned = 1, actioned_at = ? WHERE customer_id = ?",
        (now_iso, customer_id),
    )
    conn.commit()
    conn.close()

    log_audit_event(
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="RETENTION_ACTION_TAKEN",
        target_resource=f"customer:{customer_id}",
        details=f"Marked action taken at {now_iso}",
    )

    return {"status": "SUCCESS", "customer_id": customer_id, "actioned_at": now_iso}
