"""Authentication Endpoints (TICKET-601)."""

from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.core.rbac import UserContext, get_current_user
from backend.app.core.security import create_access_token
from backend.app.schemas.auth import LoginRequest, TokenResponse, UserProfileResponse

router = APIRouter()

# Mock users for local development SSO testing
MOCK_USERS = {
    "executive@telecom.com": {"user_id": "usr-101", "name": "Sarah Executive", "role": "Executive"},
    "manager@telecom.com": {"user_id": "usr-102", "name": "John Retention", "role": "RetentionManager"},
    "analyst@telecom.com": {"user_id": "usr-103", "name": "Alex DataAnalyst", "role": "Analyst"},
    "admin@telecom.com": {"user_id": "usr-104", "name": "Dev Admin", "role": "Admin"},
}


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    """Authenticate user via SSO / Mock credentials."""
    user = MOCK_USERS.get(payload.email)
    if not user:
        # Default fallback role assignment if custom email entered
        user = {"user_id": "usr-999", "name": payload.email.split("@")[0].title(), "role": "RetentionManager"}

    token = create_access_token(
        subject={"sub": user["user_id"], "email": payload.email, "role": user["role"]}
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user["user_id"],
        email=payload.email,
        role=user["role"],
    )


@router.get("/auth/me", response_model=UserProfileResponse)
def get_current_user_profile(current_user: UserContext = Depends(get_current_user)):
    """Get current authenticated user session details."""
    return UserProfileResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        name=current_user.email.split("@")[0].title(),
        role=current_user.role,
    )
