"""Production Authentication Endpoints (TASK 17).

Provides:
  - POST /auth/login: Authenticate against DB credentials with brute-force lockout & audit logging
  - POST /auth/refresh: Exchange valid refresh token for fresh access token
  - POST /auth/logout: Audit and terminate authenticated session
  - GET /auth/me: Retrieve current user identity and permissions
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.core.audit import log_audit_event
from backend.app.core.config import settings
from backend.app.core.crypto import verify_password
from backend.app.core.rbac import (
    ROLE_PERMISSIONS,
    UserContext,
    get_current_user,
)
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
)
from backend.app.db.session import get_db
from backend.app.db.repositories.user_repo import UserRepository
from backend.app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserProfileResponse,
)

router = APIRouter()


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Authenticate user with email/username and password."""
    user_repo = UserRepository(db)
    identifier = payload.email.strip().lower()
    
    # Try finding user by email or username
    user = user_repo.get_by_email(identifier) or user_repo.get_by_username(identifier)
    
    # Generic error message to prevent user enumeration
    invalid_credentials_detail = "Invalid email/username or password."

    if not user:
        log_audit_event(
            actor_email=identifier,
            actor_role="Anonymous",
            action="AUTH_LOGIN_FAILURE",
            target_resource="auth:login",
            details="Login attempt failed: user not found",
            request_id=request.headers.get("X-Request-ID"),
            event_type="AUTH_LOGIN_FAILURE",
            status="FAILURE",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=invalid_credentials_detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check account active status
    if not user.is_active:
        log_audit_event(
            actor_email=user.email,
            actor_role=user.role,
            action="AUTH_LOGIN_FAILURE",
            target_resource="auth:login",
            details="Login blocked: account is inactive",
            request_id=request.headers.get("X-Request-ID"),
            event_type="AUTH_LOGIN_FAILURE",
            status="FAILURE",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact an administrator.",
        )

    # Check lockout status
    if user.is_locked():
        log_audit_event(
            actor_email=user.email,
            actor_role=user.role,
            action="AUTH_ACCOUNT_LOCKED",
            target_resource="auth:login",
            details="Login blocked: account is locked",
            request_id=request.headers.get("X-Request-ID"),
            event_type="AUTH_ACCOUNT_LOCKED",
            status="FAILURE",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is temporarily locked due to consecutive failed attempts. Please try again later.",
        )

    # Verify password hash
    if not verify_password(payload.password, user.password_hash):
        locked = user_repo.record_login_failure(
            user,
            max_attempts=settings.MAX_FAILED_LOGIN_ATTEMPTS,
            lockout_minutes=settings.ACCOUNT_LOCKOUT_MINUTES,
        )
        if locked:
            log_audit_event(
                actor_email=user.email,
                actor_role=user.role,
                action="AUTH_ACCOUNT_LOCKED",
                target_resource="auth:login",
                details=f"Account locked after {settings.MAX_FAILED_LOGIN_ATTEMPTS} failed attempts",
                request_id=request.headers.get("X-Request-ID"),
                event_type="AUTH_ACCOUNT_LOCKED",
                status="FAILURE",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account has been temporarily locked due to multiple failed login attempts.",
            )

        log_audit_event(
            actor_email=user.email,
            actor_role=user.role,
            action="AUTH_LOGIN_FAILURE",
            target_resource="auth:login",
            details="Login attempt failed: invalid password",
            request_id=request.headers.get("X-Request-ID"),
            event_type="AUTH_LOGIN_FAILURE",
            status="FAILURE",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=invalid_credentials_detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Record login success
    user_repo.record_login_success(user)

    # Generate tokens
    access_token = create_access_token(
        subject={"sub": user.id, "email": user.email, "role": user.role}
    )
    refresh_token = create_refresh_token(
        subject={"sub": user.id, "email": user.email}
    )

    permissions = list(ROLE_PERMISSIONS.get(user.role, set()))

    log_audit_event(
        actor_email=user.email,
        actor_role=user.role,
        action="AUTH_LOGIN_SUCCESS",
        target_resource="auth:login",
        details="User authenticated successfully",
        request_id=request.headers.get("X-Request-ID"),
        event_type="AUTH_LOGIN_SUCCESS",
        status="SUCCESS",
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        permissions=permissions,
    )


@router.post("/auth/refresh", response_model=TokenResponse)
def refresh_token_endpoint(
    payload: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Exchange a valid refresh token for a new access token."""
    try:
        token_payload = decode_access_token(payload.refresh_token, expected_type="refresh")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired refresh token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = token_payload.get("sub")
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id) if user_id else None

    if not user or not user.is_active or user.is_locked():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User session is invalid or account is disabled.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    new_access_token = create_access_token(
        subject={"sub": user.id, "email": user.email, "role": user.role}
    )
    new_refresh_token = create_refresh_token(
        subject={"sub": user.id, "email": user.email}
    )

    permissions = list(ROLE_PERMISSIONS.get(user.role, set()))

    log_audit_event(
        actor_email=user.email,
        actor_role=user.role,
        action="AUTH_TOKEN_REFRESH",
        target_resource="auth:refresh",
        details="Access token refreshed successfully",
        request_id=request.headers.get("X-Request-ID"),
        event_type="AUTH_TOKEN_REFRESH",
        status="SUCCESS",
    )

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        permissions=permissions,
    )


@router.post("/auth/logout")
def logout(
    request: Request,
    current_user: UserContext = Depends(get_current_user),
):
    """Terminate the current user session and record audit event."""
    log_audit_event(
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="AUTH_LOGOUT",
        target_resource="auth:logout",
        details="User logged out",
        request_id=request.headers.get("X-Request-ID"),
        event_type="AUTH_LOGOUT",
        status="SUCCESS",
    )
    return {"message": "Session terminated successfully"}


@router.get("/auth/me", response_model=UserProfileResponse)
def get_current_user_profile(
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current authenticated user identity, role, and permission grants."""
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(current_user.user_id)
    
    return UserProfileResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        username=current_user.username,
        name=user.full_name if user else current_user.email.split("@")[0].title(),
        role=current_user.role,
        permissions=list(current_user.permissions),
        is_active=user.is_active if user else True,
        created_at=user.created_at.isoformat() if user and user.created_at else None,
        last_login_at=user.last_login_at.isoformat() if user and user.last_login_at else None,
    )
