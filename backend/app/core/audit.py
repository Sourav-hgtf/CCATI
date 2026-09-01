"""Audit Logging Module (TICKET-604, TASK 12, TASK 20 PostgreSQL).

Records security-sensitive and business-critical actions:
  - PII reveals / data exports
  - Model promotions / integrity checks
  - Scoring jobs / batch runs
  - Prediction completions and rejections
  - Data-quality gate decisions
  - Drift and performance alert triggers
"""

from datetime import datetime, timezone, timedelta
from typing import Any
import logging
from backend.app.core.config import settings
from backend.app.db.models.audit import AuditLog
from backend.app.db.session import SessionLocal

logger = logging.getLogger("telecom_churn.audit")

# ── Recognised event types ────────────────────────────────────────────────────
EVENT_TYPES = {
    # Prediction lifecycle
    "PREDICTION_REQUESTED",
    "PREDICTION_COMPLETED",
    "PREDICTION_REJECTED_DATA_QUALITY",
    "PREDICTION_REJECTED_AUTH",
    # Model management
    "MODEL_LOADED",
    "MODEL_INTEGRITY_VERIFIED",
    "MODEL_INTEGRITY_FAILED",
    "MODEL_PROMOTION",
    # Monitoring operations
    "MONITORING_RUN",
    "DRIFT_ALERT_TRIGGERED",
    "PERFORMANCE_EVALUATION",
    "PERFORMANCE_DEGRADATION_DETECTED",
    # Data operations
    "DATA_QUALITY_VALIDATION",
    "DATA_QUALITY_FAILURE",
    "SCORING_JOB_TRIGGERED",
    # Authentication and Access Control (TASK 17)
    "AUTH_LOGIN_SUCCESS",
    "AUTH_LOGIN_FAILURE",
    "AUTH_LOGOUT",
    "AUTH_TOKEN_REFRESH",
    "AUTH_ACCOUNT_LOCKED",
    "AUTH_PERMISSION_DENIED",
    "USER_CREATED",
    "USER_ROLE_UPDATED",
    "USER_STATUS_UPDATED",
    "USER_PASSWORD_CHANGED",
    # Generic
    "TRIGGER_SCORING_JOB",
    "ROI_SIMULATION",
    "RETENTION_RECOMMENDATION",
    "DATA_EXPORT",
    "ADMIN_ACTION",
}


def log_audit_event(
    actor_email: str,
    actor_role: str,
    action: str,
    target_resource: str,
    details: str = "",
    *,
    request_id: str | None = None,
    model_version: str | None = None,
    event_type: str | None = None,
    status: str = "SUCCESS",
) -> None:
    """Write a structured audit log entry."""
    if not settings.ENABLE_AUDIT_LOGGING:
        return

    etype = event_type if event_type in EVENT_TYPES else action

    session = SessionLocal()
    try:
        log_entry = AuditLog(
            timestamp=datetime.now(timezone.utc).isoformat(),
            actor_email=actor_email,
            actor_role=actor_role,
            action=action,
            target_resource=target_resource,
            details=details,
            request_id=request_id,
            model_version=model_version,
            event_type=etype,
            status=status,
        )
        session.add(log_entry)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to write audit log: {e}")
    finally:
        session.close()


def get_audit_logs(limit: int = 100) -> list[dict[str, Any]]:
    """Retrieve recent audit logs for the Admin viewer (backward-compatible)."""
    return get_audit_events(limit=limit)


def get_audit_events(
    limit: int = 100,
    event_type: str | None = None,
    status: str | None = None,
    model_version: str | None = None,
    since_iso: str | None = None,
    until_iso: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieve audit events with optional filters."""
    session = SessionLocal()
    try:
        query = session.query(AuditLog)

        if event_type:
            query = query.filter(AuditLog.event_type == event_type)
        if status:
            query = query.filter(AuditLog.status == status)
        if model_version:
            query = query.filter(AuditLog.model_version == model_version)
        if since_iso:
            query = query.filter(AuditLog.timestamp >= since_iso)
        if until_iso:
            query = query.filter(AuditLog.timestamp <= until_iso)

        rows = query.order_by(AuditLog.id.desc()).limit(limit).all()

        return [
            {
                "id": r.id,
                "timestamp": r.timestamp,
                "actor_email": r.actor_email,
                "actor_role": r.actor_role,
                "action": r.action,
                "target_resource": r.target_resource,
                "details": r.details,
                "request_id": r.request_id,
                "model_version": r.model_version,
                "event_type": r.event_type,
                "status": r.status,
            }
            for r in rows
        ]
    finally:
        session.close()


def purge_old_audit_events(retention_days: int | None = None) -> int:
    """Delete audit records older than *retention_days* days."""
    days = retention_days if retention_days is not None else settings.AUDIT_RETENTION_DAYS
    if days <= 0:
        return 0

    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    session = SessionLocal()
    try:
        deleted = session.query(AuditLog).filter(AuditLog.timestamp < cutoff).delete()
        session.commit()
        return deleted
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to purge old audit events: {e}")
        return 0
    finally:
        session.close()
