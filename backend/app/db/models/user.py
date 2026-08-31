"""User ORM Model (TASK 17 - Production Authentication & RBAC)."""

from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from backend.app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="Viewer", index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    last_login_at = Column(DateTime, nullable=True)

    def is_locked(self) -> bool:
        """Check if account is currently locked out."""
        if self.locked_until is None:
            return False
        # If locked_until is naive or timezone-aware, compare accurately
        now = datetime.now(timezone.utc)
        if self.locked_until.tzinfo is None:
            return self.locked_until > datetime.now(timezone.utc).replace(tzinfo=None)
        return self.locked_until > now
