"""Pydantic Schemas for Auth Endpoints."""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str = "password"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: str


class UserProfileResponse(BaseModel):
    user_id: str
    email: str
    name: str
    role: str
