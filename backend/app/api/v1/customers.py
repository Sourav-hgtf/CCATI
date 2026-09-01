"""Customer Endpoints (TICKET-502, TICKET-503, TICKET-603, TICKET-704, TASK 20 PostgreSQL)."""

from datetime import datetime, timezone
import json
import math
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, desc, asc
from sqlalchemy.orm import Session

from backend.app.core.audit import log_audit_event
from backend.app.core.config import settings
from backend.app.core.logger import get_logger
from backend.app.core.rate_limiter import rate_limit_admin, rate_limit_read
from backend.app.core.rbac import UserContext, get_current_user, require_roles
from backend.app.core.security import mask_email, mask_name, mask_phone
from backend.app.db.models.customer import CallLog, CustomerScore
from backend.app.db.session import get_db
from backend.app.schemas.customer import (
    CustomerDetailResponse,
    CustomerListItem,
    CustomerPaginatedResponse,
)

router = APIRouter()
logger = get_logger("telecom_churn.customers")


@router.get("/customers", response_model=CustomerPaginatedResponse, dependencies=[Depends(rate_limit_read)])
def get_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    risk_tier: str | None = None,
    plan_tier: str | None = None,
    segment_id: int | None = None,
    search: str | None = None,
    sort_by: str = Query("priority_score", pattern="^(priority_score|churn_probability|tenure_months|monthly_charges)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: UserContext = Depends(require_roles(["Admin", "RetentionManager", "Analyst", "Operations", "Viewer", "Executive"])),
    db: Session = Depends(get_db),
):
    """TICKET-502: GET /api/v1/customers (paginated, filterable, sortable)."""
    query = db.query(CustomerScore)

    if risk_tier:
        query = query.filter(CustomerScore.risk_tier == risk_tier)
    if plan_tier:
        query = query.filter(CustomerScore.plan_tier == plan_tier)
    if segment_id is not None:
        query = query.filter(CustomerScore.cluster_id == segment_id)
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                CustomerScore.customer_id.ilike(search_pattern),
                CustomerScore.name.ilike(search_pattern),
            )
        )

    total_records = query.count()

    # Sort column
    sort_col = getattr(CustomerScore, sort_by, CustomerScore.priority_score)
    order_func = desc if sort_order.lower() == "desc" else asc
    query = query.order_by(order_func(sort_col))

    offset = (page - 1) * page_size
    records = query.offset(offset).limit(page_size).all()

    items = []
    for r in records:
        rec_data = json.loads(r.recommendation_json) if r.recommendation_json else {}
        items.append(
            CustomerListItem(
                customer_id=r.customer_id,
                name=mask_name(r.name),  # Mask PII by default in list views
                phone=mask_phone(r.phone),
                plan_tier=r.plan_tier,
                tenure_months=r.tenure_months,
                monthly_charges=r.monthly_charges,
                churn_probability=r.churn_probability,
                risk_tier=r.risk_tier,
                priority_score=r.priority_score,
                usage_drop_call_pct=r.usage_drop_call_pct,
                support_calls_m1=r.support_calls_m1,
                recommended_action=rec_data.get("action_name", "Standard Engagement"),
                segment_id=r.cluster_id,
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


@router.get("/customers/{customer_id}", response_model=CustomerDetailResponse, dependencies=[Depends(rate_limit_read)])
def get_customer_detail(
    customer_id: str,
    reveal_pii: bool = False,
    current_user: UserContext = Depends(require_roles(["Admin", "RetentionManager", "Analyst", "Operations", "Viewer", "Executive"])),
    db: Session = Depends(get_db),
):
    # Check PII permissions before executing database query
    if reveal_pii and current_user.role not in ["RetentionManager", "Admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Unmasking PII is restricted to RetentionManager and Admin roles. Current role: '{current_user.role}'",
        )

    row = db.query(CustomerScore).filter(CustomerScore.customer_id == customer_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Customer record not found")

    # Fetch call logs for history
    call_rows = db.query(CallLog).filter(CallLog.customer_id == customer_id).all()
    call_logs = [
        {
            "call_reason": c.call_reason,
            "sentiment": c.sentiment,
            "resolved": c.resolved,
            "duration_sec": c.duration_sec,
        }
        for c in call_rows
    ]

    raw_shap = json.loads(row.shap_json) if row.shap_json else []
    if isinstance(raw_shap, dict):
        shap_features = raw_shap.get("top_features", [])
    elif isinstance(raw_shap, list):
        shap_features = raw_shap
    else:
        shap_features = []
        
    rec_payload = json.loads(row.recommendation_json) if row.recommendation_json else {}
    rec_payload["actioned"] = bool(row.actioned)
    rec_payload["actioned_at"] = row.actioned_at

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
    usage_drop = row.usage_drop_call_pct or 0.0
    support_m1 = row.support_calls_m1 or 0
    usage_history = [
        {"month": "M-3", "call_minutes": round(usage_drop * 100, 1), "support_calls": max(0, support_m1 - 2)},
        {"month": "M-2", "call_minutes": round(usage_drop * 50, 1), "support_calls": max(0, support_m1 - 1)},
        {"month": "M-1", "call_minutes": usage_drop, "support_calls": support_m1},
    ]

    return CustomerDetailResponse(
        customer_id=row.customer_id,
        name=row.name if not should_mask else mask_name(row.name),
        phone=row.phone if not should_mask else mask_phone(row.phone),
        email=row.email if not should_mask else mask_email(row.email),
        is_pii_revealed=not should_mask,
        plan_tier=row.plan_tier,
        contract_type=row.contract_type,
        payment_method=row.payment_method,
        tenure_months=row.tenure_months,
        monthly_charges=row.monthly_charges,
        total_charges=row.total_charges,
        churn_probability=row.churn_probability,
        risk_tier=row.risk_tier,
        priority_score=row.priority_score,
        clv=row.clv,
        usage_history=usage_history,
        top_shap_features=shap_features,
        recommendation=rec_payload,
        call_log_history=call_logs,
        segment_id=row.cluster_id,
    )


@router.post("/customers/{customer_id}/action", dependencies=[Depends(rate_limit_admin)])
def mark_customer_actioned(
    customer_id: str,
    current_user: UserContext = Depends(require_roles(["RetentionManager", "Admin"])),
    db: Session = Depends(get_db),
):
    """TICKET-704: Mark retention recommendation as actioned."""
    row = db.query(CustomerScore).filter(CustomerScore.customer_id == customer_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Customer record not found")

    now_iso = datetime.now(timezone.utc).isoformat()
    row.actioned = 1
    row.actioned_at = now_iso
    db.commit()

    log_audit_event(
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="RETENTION_ACTION_TAKEN",
        target_resource=f"customer:{customer_id}",
        details=f"Marked action taken at {now_iso}",
    )

    return {"status": "SUCCESS", "customer_id": customer_id, "actioned_at": now_iso}
