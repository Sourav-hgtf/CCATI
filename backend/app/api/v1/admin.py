"""Admin Endpoints (TICKET-604, TICKET-804)."""

from fastapi import APIRouter, Depends
from backend.app.core.audit import get_audit_logs
from backend.app.core.rbac import UserContext, require_roles

router = APIRouter()


@router.get("/admin/audit-logs")
def get_system_audit_logs(
    limit: int = 100,
    current_user: UserContext = Depends(require_roles(["Admin"])),
):
    """TICKET-604: Retrieve security audit logs (Admin only)."""
    logs = get_audit_logs(limit=limit)
    return {"total": len(logs), "logs": logs}


@router.get("/admin/users")
def get_user_roles(
    current_user: UserContext = Depends(require_roles(["Admin"])),
):
    """TICKET-804: Get list of system users and role assignments."""
    users = [
        {"user_id": "usr-101", "name": "Sarah Executive", "email": "executive@telecom.com", "role": "Executive", "status": "Active"},
        {"user_id": "usr-102", "name": "John Retention", "email": "manager@telecom.com", "role": "RetentionManager", "status": "Active"},
        {"user_id": "usr-103", "name": "Alex DataAnalyst", "email": "analyst@telecom.com", "role": "Analyst", "status": "Active"},
        {"user_id": "usr-104", "name": "Dev Admin", "email": "admin@telecom.com", "role": "Admin", "status": "Active"},
    ]
    return {"users": users}
