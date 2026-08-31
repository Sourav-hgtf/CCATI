"""Cryptography and Password Security Utilities (TASK 17).

Provides secure password hashing using bcrypt, verification, and password
strength validation without leaking sensitive credentials in error messages.
"""

import re
# pyrefly: ignore [missing-import]
import bcrypt


def get_password_hash(password: str) -> str:
    """Hash a plaintext password using bcrypt with automated salt generation."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify that a plaintext password matches the stored bcrypt hash."""
    if not plain_password or not hashed_password:
        return False
    try:
        password_bytes = plain_password.encode("utf-8")
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception:
        return False


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password against baseline security requirements.
    
    Requirements:
      - Minimum 8 characters
      - At least one letter
      - At least one number or special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Za-z]", password):
        return False, "Password must contain at least one letter."
    if not re.search(r"[0-9!@#$%^&*()_+\-=\[\]{};':\",.<>/?\\|`~]", password):
        return False, "Password must contain at least one number or special character."
    return True, ""
