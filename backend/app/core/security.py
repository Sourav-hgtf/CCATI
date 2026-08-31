"""Security, Authentication, JWT, and PII Masking Utilities (TICKET-601, TICKET-603)."""

from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
from backend.app.core.config import settings


def create_access_token(subject: str | dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Generate JWT Access Token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    if isinstance(subject, dict):
        to_encode = subject.copy()
        to_encode.update({"exp": expire})
    else:
        to_encode = {"sub": str(subject), "exp": expire}

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate JWT Access Token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise ValueError("Invalid token")


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
