"""Audit Logging Module (TICKET-604, TASK 12).

Records security-sensitive and business-critical actions:
  - PII reveals / data exports
  - Model promotions / integrity checks
  - Scoring jobs / batch runs
  - Prediction completions and rejections
  - Data-quality gate decisions
  - Drift and performance alert triggers

Table: audit_logs
Columns added in TASK 12:
  request_id     – propagated from X-Request-ID correlation header
  model_version  – active model version at time of event
  event_type     – structured category (see EVENT_TYPES below)
  status         – SUCCESS | FAILURE | WARNING | INFO
"""

from datetime import datetime, timezone, timedelta
from pathlib import Path
import sqlite3
from typing import Any

from backend.app.core.config import settings

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

# ── Internal DB helper ────────────────────────────────────────────────────────

def _get_audit_conn() -> sqlite3.Connection:
    """Return a connection with the audit_logs table guaranteed to exist."""
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    # Create table with all columns (idempotent)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp       TEXT NOT NULL,
            actor_email     TEXT NOT NULL,
            actor_role      TEXT NOT NULL,
            action          TEXT NOT NULL,
            target_resource TEXT NOT NULL,
            details         TEXT,
            request_id      TEXT,
            model_version   TEXT,
            event_type      TEXT,
            status          TEXT DEFAULT 'SUCCESS'
        )
    """)
    # Add new columns to existing databases that predate TASK 12
    existing_cols = {
        row[1] for row in conn.execute("PRAGMA table_info(audit_logs)").fetchall()
    }
    for col, definition in [
        ("request_id",    "TEXT"),
        ("model_version", "TEXT"),
        ("event_type",    "TEXT"),
        ("status",        "TEXT DEFAULT 'SUCCESS'"),
    ]:
        if col not in existing_cols:
            conn.execute(f"ALTER TABLE audit_logs ADD COLUMN {col} {definition}")

    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_audit_event_type  ON audit_logs(event_type)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_audit_status       ON audit_logs(status)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_audit_timestamp    ON audit_logs(timestamp)"
    )
    conn.commit()
    return conn


# ── Public write API ──────────────────────────────────────────────────────────

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
    """Write a structured audit log entry.

    Parameters
    ----------
    actor_email:      Email of the authenticated user performing the action.
    actor_role:       Role of that user (Admin, Analyst, …).
    action:           Free-text action label (preserved for backward compat).
    target_resource:  The entity being acted on (e.g. "model:v1.0.0").
    details:          Optional human-readable detail string. Do NOT include PII.
    request_id:       Correlation ID from the HTTP request.
    model_version:    Active model version at the time of the event.
    event_type:       Structured event category from EVENT_TYPES.
    status:           "SUCCESS" | "FAILURE" | "WARNING" | "INFO".
    """
    if not settings.ENABLE_AUDIT_LOGGING:
        return

    # Normalise event_type — fall back to action if not provided
    etype = event_type if event_type in EVENT_TYPES else action

    conn = _get_audit_conn()
    try:
        conn.execute(
            """
            INSERT INTO audit_logs
                (timestamp, actor_email, actor_role, action, target_resource,
                 details, request_id, model_version, event_type, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                actor_email,
                actor_role,
                action,
                target_resource,
                details,
                request_id,
                model_version,
                etype,
                status,
            ),
        )
        conn.commit()
    finally:
        conn.close()


# ── Public read API ───────────────────────────────────────────────────────────

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
    """Retrieve audit events with optional filters.

    Parameters
    ----------
    limit:         Maximum number of records to return.
    event_type:    Filter by structured event category.
    status:        Filter by status ("SUCCESS", "FAILURE", …).
    model_version: Filter by model version string.
    since_iso:     ISO-8601 lower bound on timestamp (inclusive).
    until_iso:     ISO-8601 upper bound on timestamp (inclusive).
    """
    conn = _get_audit_conn()
    try:
        clauses: list[str] = []
        params: list[Any] = []

        if event_type:
            clauses.append("event_type = ?")
            params.append(event_type)
        if status:
            clauses.append("status = ?")
            params.append(status)
        if model_version:
            clauses.append("model_version = ?")
            params.append(model_version)
        if since_iso:
            clauses.append("timestamp >= ?")
            params.append(since_iso)
        if until_iso:
            clauses.append("timestamp <= ?")
            params.append(until_iso)

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        params.append(limit)

        cursor = conn.execute(
            f"""
            SELECT id, timestamp, actor_email, actor_role, action,
                   target_resource, details, request_id, model_version,
                   event_type, status
            FROM audit_logs
            {where}
            ORDER BY id DESC
            LIMIT ?
            """,
            params,
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    return [
        {
            "id":              r["id"],
            "timestamp":       r["timestamp"],
            "actor_email":     r["actor_email"],
            "actor_role":      r["actor_role"],
            "action":          r["action"],
            "target_resource": r["target_resource"],
            "details":         r["details"],
            "request_id":      r["request_id"],
            "model_version":   r["model_version"],
            "event_type":      r["event_type"],
            "status":          r["status"],
        }
        for r in rows
    ]


# ── Retention helper ──────────────────────────────────────────────────────────

def purge_old_audit_events(retention_days: int | None = None) -> int:
    """Delete audit records older than *retention_days* days.

    Uses ``settings.AUDIT_RETENTION_DAYS`` when *retention_days* is not given.
    Returns the number of rows deleted.  Does nothing if retention_days == 0.
    """
    days = retention_days if retention_days is not None else settings.AUDIT_RETENTION_DAYS
    if days <= 0:
        return 0

    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    conn = _get_audit_conn()
    try:
        cursor = conn.execute(
            "DELETE FROM audit_logs WHERE timestamp < ?", (cutoff,)
        )
        conn.commit()
        deleted = cursor.rowcount
    finally:
        conn.close()
    return deleted
