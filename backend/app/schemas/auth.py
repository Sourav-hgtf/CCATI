"""Pydantic Schemas for Auth, RBAC and Admin User Management (TASK 17)."""

from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email or username")
    password: str = Field(..., min_length=1, description="User plaintext password")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Valid refresh token")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    user_id: str
    email: str
    username: str
    full_name: str
    role: str
    permissions: list[str] = []


class UserProfileResponse(BaseModel):
    user_id: str
    email: str
    username: str
    name: str
    role: str
    permissions: list[str] = []
    is_active: bool = True
    created_at: Optional[str] = None
    last_login_at: Optional[str] = None


class CreateUserRequest(BaseModel):
    email: str = Field(..., description="Unique email address")
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    full_name: str = Field(..., min_length=2, max_length=100, description="User full name")
    password: str = Field(..., min_length=8, description="Password (min 8 chars)")
    role: str = Field("Viewer", description="System role: Admin, RetentionManager, Analyst, ModelManager, Operations, Viewer")


class UpdateUserRoleRequest(BaseModel):
    role: str = Field(..., description="New role for the user")


class UpdateUserStatusRequest(BaseModel):
    is_active: bool = Field(..., description="Active status flag")


class UserResponse(BaseModel):
    user_id: str
    email: str
    username: str
    name: str
    role: str
    status: str
    is_active: bool
    created_at: Optional[str] = None
    last_login_at: Optional[str] = None
