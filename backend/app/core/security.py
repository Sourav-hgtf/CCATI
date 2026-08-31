"""Security, Authentication, JWT, and PII Masking Utilities (TASK 17 Hardened).

Supports:
  - Cryptographically secure Access Tokens (short-lived)
  - Cryptographically secure Refresh Tokens (long-lived)
  - Strict Token Decoding & Claim Verification
  - Zero tolerance for mock bypasses
  - PII Masking for compliance (GDPR/CPRA)
"""

from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
from backend.app.core.config import settings


def create_access_token(subject: str | dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Generate cryptographically signed JWT Access Token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    if isinstance(subject, dict):
        to_encode = subject.copy()
        to_encode.update({"exp": expire, "type": "access"})
    else:
        to_encode = {"sub": str(subject), "exp": expire, "type": "access"}

    encoded_jwt = jwt.encode(to_encode, settings.get_jwt_secret, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: str | dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Generate cryptographically signed JWT Refresh Token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    if isinstance(subject, dict):
        to_encode = subject.copy()
        to_encode.update({"exp": expire, "type": "refresh"})
    else:
        to_encode = {"sub": str(subject), "exp": expire, "type": "refresh"}

    encoded_jwt = jwt.encode(to_encode, settings.get_jwt_secret, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    """Strictly decode and validate JWT token claims and signature."""
    try:
        payload = jwt.decode(
            token,
            settings.get_jwt_secret,
            algorithms=[settings.ALGORITHM],
            options={"require": ["exp", "sub"]}
        )
        token_type = payload.get("type", "access")
        if expected_type and token_type != expected_type:
            raise ValueError(f"Invalid token type: expected {expected_type}, got {token_type}")
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token signature or payload")


def mask_name(name: str) -> str:
    """Mask customer full name for PII protection."""
    if not name:
        return "Customer"
    parts = name.split()
    masked_parts = [p[0] + "*" * (len(p) - 1) if len(p) > 1 else p for p in parts]
    return " ".join(masked_parts)


def mask_phone(phone: str) -> str:
    """Mask phone number: +91-98765-12345 -> +91-XXXXX-12345."""
    if not phone or len(phone) < 8:
        return "+XX-XXXXX-XXXX"
    return phone[:4] + "-XXXXX-" + phone[-4:]


def mask_email(email: str) -> str:
    """Mask email address: user123@example.com -> u***3@example.com."""
    if not email or "@" not in email:
        return "u***@example.com"
    name, domain = email.split("@", 1)
    if len(name) <= 2:
        masked_name = name[0] + "*"
    else:
        masked_name = name[0] + "*" * (len(name) - 2) + name[-1]
    return f"{masked_name}@{domain}"
