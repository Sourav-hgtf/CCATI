"""Admin Endpoints (TASK 17 - Production User Management & RBAC Administration).

Provides:
  - GET /admin/audit-logs: Retrieve security audit logs (Admin only)
  - GET /admin/users: List all system users with roles and status (Admin only)
  - POST /admin/users: Create a new system user with password validation (Admin only)
  - PATCH /admin/users/{id}/role: Update a user's role with admin demotion guard (Admin only)
  - PATCH /admin/users/{id}/status: Activate/Deactivate user with admin lockout guard (Admin only)
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.core.audit import get_audit_logs, log_audit_event
from backend.app.core.crypto import get_password_hash, validate_password_strength
from backend.app.core.rate_limiter import rate_limit_admin
from backend.app.core.rbac import (
    ALL_ROLES,
    ROLE_ADMIN,
    UserContext,
    require_roles,
)
from backend.app.db.session import get_db
from backend.app.db.repositories.user_repo import UserRepository
from backend.app.schemas.auth import (
    CreateUserRequest,
    UpdateUserRoleRequest,
    UpdateUserStatusRequest,
    UserResponse,
)

router = APIRouter()


@router.get("/admin/audit-logs", dependencies=[Depends(rate_limit_admin)])
def get_system_audit_logs(
    limit: int = 100,
    current_user: UserContext = Depends(require_roles([ROLE_ADMIN])),
):
    """Retrieve security and business audit logs (Admin only)."""
    logs = get_audit_logs(limit=limit)
    return {"total": len(logs), "logs": logs}


@router.get("/admin/users", response_model=dict, dependencies=[Depends(rate_limit_admin)])
def list_system_users(
    current_user: UserContext = Depends(require_roles([ROLE_ADMIN])),
    db: Session = Depends(get_db),
):
    """List all registered system users and their active role assignments (Admin only)."""
    repo = UserRepository(db)
    users = repo.get_all()
    user_list = [
        UserResponse(
            user_id=u.id,
            email=u.email,
            username=u.username,
            name=u.full_name,
            role=u.role,
            status="Active" if u.is_active else "Inactive",
            is_active=u.is_active,
            created_at=u.created_at.isoformat() if u.created_at else None,
            last_login_at=u.last_login_at.isoformat() if u.last_login_at else None,
        ).model_dump()
        for u in users
    ]
    return {"total": len(user_list), "users": user_list}


@router.post("/admin/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(rate_limit_admin)])
def create_system_user(
    payload: CreateUserRequest,
    request: Request,
    current_user: UserContext = Depends(require_roles([ROLE_ADMIN])),
    db: Session = Depends(get_db),
):
    """Create a new system user with role assignment (Admin only)."""
    repo = UserRepository(db)
    
    # Check for existing email or username
    if repo.get_by_email(payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists.",
        )
    if repo.get_by_username(payload.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this username already exists.",
        )

    # Validate role
    if payload.role not in ALL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{payload.role}'. Must be one of: {ALL_ROLES}",
        )

    # Validate password complexity
    valid_pw, pw_err = validate_password_strength(payload.password)
    if not valid_pw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=pw_err,
        )

    user_id = f"usr-{uuid.uuid4().hex[:8]}"
    password_hash = get_password_hash(payload.password)
    new_user = repo.create_user(
        user_id=user_id,
        email=payload.email,
        username=payload.username,
        full_name=payload.full_name,
        password_hash=password_hash,
        role=payload.role,
        is_active=True,
    )

    log_audit_event(
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="USER_CREATED",
        target_resource=f"user:{new_user.id}",
        details=f"Created user {new_user.email} with role {new_user.role}",
        request_id=request.headers.get("X-Request-ID"),
        event_type="USER_CREATED",
        status="SUCCESS",
    )

    return UserResponse(
        user_id=new_user.id,
        email=new_user.email,
        username=new_user.username,
        name=new_user.full_name,
        role=new_user.role,
        status="Active" if new_user.is_active else "Inactive",
        is_active=new_user.is_active,
        created_at=new_user.created_at.isoformat() if new_user.created_at else None,
        last_login_at=None,
    )


@router.patch("/admin/users/{user_id}/role", response_model=UserResponse, dependencies=[Depends(rate_limit_admin)])
def update_user_role(
    user_id: str,
    payload: UpdateUserRoleRequest,
    request: Request,
    current_user: UserContext = Depends(require_roles([ROLE_ADMIN])),
    db: Session = Depends(get_db),
):
    """Update a user's role assignment (Admin only). Guard against demoting last active Admin."""
    repo = UserRepository(db)
    target_user = repo.get_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found.",
        )

    if payload.role not in ALL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{payload.role}'. Must be one of: {ALL_ROLES}",
        )

    # Protect against removing/demoting the last active administrator
    if target_user.role == ROLE_ADMIN and payload.role != ROLE_ADMIN:
        active_admins = repo.count_active_admins()
        if active_admins <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the last active Administrator in the system.",
            )

    old_role = target_user.role
    updated = repo.update_role(target_user, payload.role)

    log_audit_event(
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="USER_ROLE_UPDATED",
        target_resource=f"user:{user_id}",
        details=f"Updated role for {updated.email} from {old_role} to {payload.role}",
        request_id=request.headers.get("X-Request-ID"),
        event_type="USER_ROLE_UPDATED",
        status="SUCCESS",
    )

    return UserResponse(
        user_id=updated.id,
        email=updated.email,
        username=updated.username,
        name=updated.full_name,
        role=updated.role,
        status="Active" if updated.is_active else "Inactive",
        is_active=updated.is_active,
        created_at=updated.created_at.isoformat() if updated.created_at else None,
        last_login_at=updated.last_login_at.isoformat() if updated.last_login_at else None,
    )


@router.patch("/admin/users/{user_id}/status", response_model=UserResponse, dependencies=[Depends(rate_limit_admin)])
def update_user_status(
    user_id: str,
    payload: UpdateUserStatusRequest,
    request: Request,
    current_user: UserContext = Depends(require_roles([ROLE_ADMIN])),
    db: Session = Depends(get_db),
):
    """Enable or disable a user account (Admin only). Guard against deactivating last active Admin."""
    repo = UserRepository(db)
    target_user = repo.get_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found.",
        )

    # Protect against deactivating the last active administrator
    if target_user.role == ROLE_ADMIN and not payload.is_active:
        active_admins = repo.count_active_admins()
        if active_admins <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate the last active Administrator in the system.",
            )

    updated = repo.update_status(target_user, payload.is_active)

    log_audit_event(
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="USER_STATUS_UPDATED",
        target_resource=f"user:{user_id}",
        details=f"Updated active status for {updated.email} to {payload.is_active}",
        request_id=request.headers.get("X-Request-ID"),
        event_type="USER_STATUS_UPDATED",
        status="SUCCESS",
    )

    return UserResponse(
        user_id=updated.id,
        email=updated.email,
        username=updated.username,
        name=updated.full_name,
        role=updated.role,
        status="Active" if updated.is_active else "Inactive",
        is_active=updated.is_active,
        created_at=updated.created_at.isoformat() if updated.created_at else None,
        last_login_at=updated.last_login_at.isoformat() if updated.last_login_at else None,
    )
