"""Observability API Endpoints (TASK 12).

Provides safe operational metrics and filterable audit event log.

Routes
------
GET  /api/v1/metrics
    – Safe snapshot of in-memory operational counters.
    – Accessible by Analyst, Admin, RetentionManager, Executive.
    – Contains NO secrets, NO PII, NO customer data.

GET  /api/v1/audit/events
    – Paginated, filterable audit trail.
    – Accessible by Analyst, Admin, RetentionManager, Executive.
    – Does NOT expose passwords, tokens, or raw customer payloads.

POST /api/v1/audit/events/purge
    – Delete audit records older than configured retention window.
    – Admin-only; respects AUDIT_RETENTION_DAYS from settings.
"""

from fastapi import APIRouter, Depends, Query
from backend.app.core.audit import get_audit_events, purge_old_audit_events
from backend.app.core.config import settings
from backend.app.core.metrics import metrics_collector
from backend.app.core.rbac import UserContext, require_roles

router = APIRouter()


@router.get("/metrics")
def get_operational_metrics(
    current_user: UserContext = Depends(
        require_roles(["Analyst", "Admin", "RetentionManager", "Executive"])
    ),
):
    """GET /api/v1/metrics — Operational metrics snapshot.

    Returns in-memory counters and latency aggregates for API, prediction,
    data-quality, drift monitoring, and model operations.

    Security: No PII, no secrets, no customer data, no stack traces.
    """
    if not settings.ENABLE_METRICS:
        return {"enabled": False, "message": "Metrics collection is disabled."}

    snapshot = metrics_collector.get_snapshot()
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.APP_ENV,
        "metrics": snapshot,
    }


@router.get("/audit/events")
def list_audit_events(
    limit: int = Query(50, ge=1, le=500),
    event_type: str | None = Query(None, description="Filter by event category"),
    status: str | None = Query(None, description="Filter by status: SUCCESS, FAILURE, WARNING, INFO"),
    model_version: str | None = Query(None, description="Filter by model version string"),
    since: str | None = Query(None, description="ISO-8601 lower timestamp bound"),
    until: str | None = Query(None, description="ISO-8601 upper timestamp bound"),
    current_user: UserContext = Depends(
        require_roles(["Analyst", "Admin", "RetentionManager", "Executive"])
    ),
):
    """GET /api/v1/audit/events — Filterable audit event log.

    Supports filtering by event_type, status, model_version, and date range.
    Results are ordered newest-first.

    Security: Does NOT expose passwords, API keys, tokens, or raw customer
    request payloads.  actor_email is included because it is an operational
    field required for traceability (non-sensitive in this internal context).
    """
    events = get_audit_events(
        limit=limit,
        event_type=event_type,
        status=status,
        model_version=model_version,
        since_iso=since,
        until_iso=until,
    )
    return {
        "total": len(events),
        "limit": limit,
        "filters": {
            "event_type": event_type,
            "status": status,
            "model_version": model_version,
            "since": since,
            "until": until,
        },
        "events": events,
    }


@router.post("/audit/events/purge")
def purge_audit_events(
    retention_days: int | None = Query(
        None,
        description="Override AUDIT_RETENTION_DAYS from settings. Must be > 0.",
        ge=1,
    ),
    current_user: UserContext = Depends(require_roles(["Admin"])),
):
    """POST /api/v1/audit/events/purge — Purge old audit records (Admin only).

    Deletes records older than *retention_days* (defaults to
    ``settings.AUDIT_RETENTION_DAYS``).  Returns the count of deleted rows.
    """
    deleted = purge_old_audit_events(retention_days=retention_days)
    effective_days = retention_days if retention_days is not None else settings.AUDIT_RETENTION_DAYS
    return {
        "status": "SUCCESS",
        "deleted_records": deleted,
        "retention_days": effective_days,
        "message": (
            f"Purged {deleted} audit record(s) older than {effective_days} day(s)."
            if deleted > 0
            else "No records fell outside the retention window."
        ),
    }
