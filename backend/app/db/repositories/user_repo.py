"""User Repository (TASK 17 - Production Authentication & RBAC)."""

from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.db.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        if not email:
            return None
        return self.db.query(User).filter(func.lower(User.email) == email.strip().lower()).first()

    def get_by_username(self, username: str) -> Optional[User]:
        if not username:
            return None
        return self.db.query(User).filter(func.lower(User.username) == username.strip().lower()).first()

    def get_all(self, limit: int = 100, offset: int = 0) -> list[User]:
        return self.db.query(User).order_by(User.created_at.asc()).offset(offset).limit(limit).all()

    def count_users(self) -> int:
        return self.db.query(User).count()

    def count_active_admins(self) -> int:
        return self.db.query(User).filter(
            User.role == "Admin",
            User.is_active.is_(True)
        ).count()

    def create_user(
        self,
        user_id: str,
        email: str,
        username: str,
        full_name: str,
        password_hash: str,
        role: str = "Viewer",
        is_active: bool = True,
    ) -> User:
        user = User(
            id=user_id,
            email=email.strip().lower(),
            username=username.strip().lower(),
            full_name=full_name.strip(),
            password_hash=password_hash,
            role=role,
            is_active=is_active,
            failed_login_attempts=0,
            locked_until=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def record_login_success(self, user: User) -> None:
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.now(timezone.utc)
        user.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(user)

    def record_login_failure(self, user: User, max_attempts: int = 5, lockout_minutes: int = 15) -> bool:
        """Increment failed attempts and lock out if threshold exceeded. Returns True if locked."""
        user.failed_login_attempts += 1
        user.updated_at = datetime.now(timezone.utc)
        locked = False
        if user.failed_login_attempts >= max_attempts:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=lockout_minutes)
            locked = True
        self.db.commit()
        self.db.refresh(user)
        return locked

    def update_role(self, user: User, new_role: str) -> User:
        user.role = new_role
        user.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_status(self, user: User, is_active: bool) -> User:
        user.is_active = is_active
        user.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(user)
        return user
