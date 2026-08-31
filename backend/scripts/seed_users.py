"""Seed Users Script (TASK 17 - Production Authentication & RBAC).

Creates canonical system users with bcrypt-hashed credentials across all defined roles.
"""

import sys
from pathlib import Path

# Ensure project root is in python path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.core.crypto import get_password_hash
from backend.app.db.base import Base
from backend.app.db.session import engine, SessionLocal
from backend.app.db.models.user import User
from backend.app.db.repositories.user_repo import UserRepository

SEED_USERS = [
    {
        "id": "usr-admin-001",
        "email": "admin@telecom.com",
        "username": "admin",
        "full_name": "Dev Admin",
        "password": "AdminPassword123!",
        "role": "Admin",
    },
    {
        "id": "usr-retention-002",
        "email": "manager@telecom.com",
        "username": "retention_manager",
        "full_name": "John Retention",
        "password": "ManagerPassword123!",
        "role": "RetentionManager",
    },
    {
        "id": "usr-analyst-003",
        "email": "analyst@telecom.com",
        "username": "data_analyst",
        "full_name": "Alex DataAnalyst",
        "password": "AnalystPassword123!",
        "role": "Analyst",
    },
    {
        "id": "usr-model-004",
        "email": "modelmanager@telecom.com",
        "username": "model_manager",
        "full_name": "Morgan ML Engineer",
        "password": "ModelPassword123!",
        "role": "ModelManager",
    },
    {
        "id": "usr-ops-005",
        "email": "operations@telecom.com",
        "username": "operations_user",
        "full_name": "Sam Operations",
        "password": "OpsPassword123!",
        "role": "Operations",
    },
    {
        "id": "usr-viewer-006",
        "email": "viewer@telecom.com",
        "username": "viewer",
        "full_name": "Valerie Viewer",
        "password": "ViewerPassword123!",
        "role": "Viewer",
    },
    {
        "id": "usr-exec-007",
        "email": "executive@telecom.com",
        "username": "executive_user",
        "full_name": "Sarah Executive",
        "password": "Password123!",
        "role": "Executive",
    },
]


def seed_database_users():
    print("Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    repo = UserRepository(db)
    created_count = 0
    updated_count = 0

    try:
        for u in SEED_USERS:
            existing = repo.get_by_email(u["email"]) or repo.get_by_username(u["username"])
            if not existing:
                repo.create_user(
                    user_id=u["id"],
                    email=u["email"],
                    username=u["username"],
                    full_name=u["full_name"],
                    password_hash=get_password_hash(u["password"]),
                    role=u["role"],
                    is_active=True,
                )
                created_count += 1
                print(f"Created seed user: {u['email']} ({u['role']})")
            else:
                # Update role and password if not active
                existing.role = u["role"]
                existing.is_active = True
                existing.password_hash = get_password_hash(u["password"])
                db.commit()
                updated_count += 1
                print(f"Updated seed user: {u['email']} ({u['role']})")

        print(f"User seeding complete: {created_count} created, {updated_count} verified/updated.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database_users()
