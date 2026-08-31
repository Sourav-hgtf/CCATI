"""Role-Based Access Control (RBAC) Dependency Guards (TICKET-602)."""

from typing import Callable
from fastapi import Depends, HTTPException, Header, status
from backend.app.core.security import decode_access_token


class UserContext:
    def __init__(self, user_id: str, email: str, role: str):
        self.user_id = user_id
        self.email = email
        self.role = role


def get_current_user(authorization: str | None = Header(None)) -> UserContext:
    """Dependency to parse and validate current user context from Auth header."""
    if not authorization:
        # Default mock fallback for unauthenticated local development testing
        return UserContext(user_id="usr-default", email="manager@telecom.com", role="RetentionManager")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth scheme")
        payload = decode_access_token(token)
        return UserContext(
            user_id=payload.get("sub", "usr-anon"),
            email=payload.get("email", "anon@telecom.com"),
            role=payload.get("role", "RetentionManager"),
        )
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization token")


def require_roles(allowed_roles: list[str]) -> Callable:
    """Factory creating dependency function that enforces allowed roles."""
    def role_checker(current_user: UserContext = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role in {allowed_roles}, but current user has '{current_user.role}'",
            )
        return current_user

    return role_checker
