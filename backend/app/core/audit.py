"""Audit Logging Module (TICKET-604).

Records security-sensitive actions (PII reveals, data exports, model promotions, scoring jobs).
"""

from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any
from backend.app.core.config import settings


def _get_audit_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            actor_email TEXT NOT NULL,
            actor_role TEXT NOT NULL,
            action TEXT NOT NULL,
            target_resource TEXT NOT NULL,
            details TEXT
        )
    """)
    conn.commit()
    return conn


def log_audit_event(
    actor_email: str,
    actor_role: str,
    action: str,
    target_resource: str,
    details: str = ""
):
    """Write audit log entry."""
    conn = _get_audit_conn()
    conn.execute(
        """
        INSERT INTO audit_logs (timestamp, actor_email, actor_role, action, target_resource, details)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now(timezone.utc).isoformat(),
            actor_email,
            actor_role,
            action,
            target_resource,
            details,
        ),
    )
    conn.commit()
    conn.close()


def get_audit_logs(limit: int = 100) -> list[dict[str, Any]]:
    """Retrieve recent audit logs for Admin viewer."""
    conn = _get_audit_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, timestamp, actor_email, actor_role, action, target_resource, details FROM audit_logs ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()

    logs = []
    for r in rows:
        logs.append({
            "id": r[0],
            "timestamp": r[1],
            "actor_email": r[2],
            "actor_role": r[3],
            "action": r[4],
            "target_resource": r[5],
            "details": r[6],
        })
    return logs
