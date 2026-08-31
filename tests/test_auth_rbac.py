"""Comprehensive Test Suite for TASK 17: Production Authentication & Role-Based Access Control (RBAC)."""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.crypto import get_password_hash, verify_password
from backend.app.core.security import create_access_token
from backend.app.db.session import SessionLocal, engine
from backend.app.db.base import Base
from backend.app.db.repositories.user_repo import UserRepository
from backend.scripts.seed_users import seed_database_users

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_database():
    """Ensure database schema and seed users are initialized before running tests."""
    Base.metadata.create_all(bind=engine)
    seed_database_users()
    yield


# ── AUTHENTICATION TESTS ──────────────────────────────────────────────────────

def test_valid_login_admin():
    """Test login with valid Admin credentials."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@telecom.com", "password": "AdminPassword123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["role"] == "Admin"
    assert data["email"] == "admin@telecom.com"
    assert "customer:read" in data["permissions"]
    assert "users:manage" in data["permissions"]


def test_valid_login_by_username():
    """Test login using username instead of email."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "retention_manager", "password": "ManagerPassword123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "RetentionManager"
    assert data["email"] == "manager@telecom.com"


def test_invalid_password_returns_401():
    """Test login with wrong password returns generic 401 error."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@telecom.com", "password": "WrongPassword999!"},
    )
    assert response.status_code == 401
    assert "Invalid email/username or password" in response.json()["detail"]


def test_nonexistent_user_returns_401():
    """Test login with non-existent user returns generic 401 error (no user enumeration)."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent_hacker@telecom.com", "password": "Password123!"},
    )
    assert response.status_code == 401
    assert "Invalid email/username or password" in response.json()["detail"]


def test_deactivated_account_blocked():
    """Test that deactivated users cannot log in (403 Forbidden)."""
    db = SessionLocal()
    repo = UserRepository(db)
    user = repo.get_by_email("viewer@telecom.com")
    assert user is not None
    repo.update_status(user, is_active=False)
    db.close()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "viewer@telecom.com", "password": "ViewerPassword123!"},
    )
    assert response.status_code == 403
    assert "deactivated" in response.json()["detail"].lower()

    # Re-enable for subsequent tests
    db = SessionLocal()
    repo = UserRepository(db)
    user = repo.get_by_email("viewer@telecom.com")
    repo.update_status(user, is_active=True)
    db.close()


def test_brute_force_lockout_protection():
    """Test account is locked after consecutive failed password attempts."""
    db = SessionLocal()
    repo = UserRepository(db)
    user = repo.get_by_email("operations@telecom.com")
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()
    db.close()

    # Attempt 5 failed logins (configured threshold)
    for _ in range(5):
        client.post(
            "/api/v1/auth/login",
            json={"email": "operations@telecom.com", "password": "WrongPassword!"},
        )

    # Next attempt should be blocked with 403 Account Locked
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "operations@telecom.com", "password": "OpsPassword123!"},
    )
    assert response.status_code == 403
    assert "locked" in response.json()["detail"].lower()

    # Reset for subsequent tests
    db = SessionLocal()
    repo = UserRepository(db)
    user = repo.get_by_email("operations@telecom.com")
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()
    db.close()


def test_token_refresh_lifecycle():
    """Test exchanging a valid refresh token for a new access token."""
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "analyst@telecom.com", "password": "AnalystPassword123!"},
    )
    assert login_res.status_code == 200
    refresh_token = login_res.json()["refresh_token"]

    refresh_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 200
    new_data = refresh_res.json()
    assert "access_token" in new_data
    assert new_data["role"] == "Analyst"


def test_get_current_user_profile():
    """Test GET /auth/me returns authenticated identity and permissions."""
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@telecom.com", "password": "AdminPassword123!"},
    )
    token = login_res.json()["access_token"]

    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "admin@telecom.com"
    assert me_data["role"] == "Admin"
    assert "permissions" in me_data


def test_unauthenticated_request_rejected():
    """Test that requests with no Bearer token or invalid tokens are rejected with 401."""
    # No header
    res_no_auth = client.get("/api/v1/auth/me")
    assert res_no_auth.status_code == 401

    # Fake header
    res_bad_auth = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer fake.tampered.token"},
    )
    assert res_bad_auth.status_code == 401


# ── ROLE-BASED ACCESS CONTROL (RBAC) TESTS ───────────────────────────────────

def test_admin_access_to_admin_endpoints():
    """Test Admin can access user management and audit logs."""
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@telecom.com", "password": "AdminPassword123!"},
    ).json()
    token = admin_login["access_token"]

    # Access users list
    res_users = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert res_users.status_code == 200
    assert "users" in res_users.json()

    # Access audit logs
    res_audit = client.get("/api/v1/admin/audit-logs", headers={"Authorization": f"Bearer {token}"})
    assert res_audit.status_code == 200
    assert "logs" in res_audit.json()


def test_non_admin_blocked_from_admin_endpoints():
    """Test Analyst and Viewer receive 403 Forbidden on Admin endpoints."""
    analyst_login = client.post(
        "/api/v1/auth/login",
        json={"email": "analyst@telecom.com", "password": "AnalystPassword123!"},
    ).json()
    analyst_token = analyst_login["access_token"]

    res_users = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {analyst_token}"})
    assert res_users.status_code == 403

    res_audit = client.get("/api/v1/admin/audit-logs", headers={"Authorization": f"Bearer {analyst_token}"})
    assert res_audit.status_code == 403


def test_pii_reveal_role_gating():
    """Test PII unmasking is restricted to Admin and RetentionManager."""
    # 1. Analyst attempting PII reveal receives 403
    analyst_login = client.post(
        "/api/v1/auth/login",
        json={"email": "analyst@telecom.com", "password": "AnalystPassword123!"},
    ).json()
    analyst_token = analyst_login["access_token"]

    res_analyst = client.get(
        "/api/v1/customers/CUST-1001?reveal_pii=true",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert res_analyst.status_code == 403

    # 2. RetentionManager attempting PII reveal succeeds (or 404 if mock cust missing, but not 403)
    mgr_login = client.post(
        "/api/v1/auth/login",
        json={"email": "manager@telecom.com", "password": "ManagerPassword123!"},
    ).json()
    mgr_token = mgr_login["access_token"]

    res_mgr = client.get(
        "/api/v1/customers/CUST-1001?reveal_pii=true",
        headers={"Authorization": f"Bearer {mgr_token}"},
    )
    # Status should NOT be 403 (could be 200 or 404 depending on database row)
    assert res_mgr.status_code in [200, 404]


def test_admin_cannot_deactivate_or_demote_last_admin():
    """Test guard preventing deactivating or demoting the last active administrator."""
    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@telecom.com", "password": "AdminPassword123!"},
    ).json()
    token = admin_login["access_token"]

    db = SessionLocal()
    repo = UserRepository(db)
    admin_user = repo.get_by_email("admin@telecom.com")
    admin_id = admin_user.id
    db.close()

    # Try deactivating the only admin
    res_deact = client.patch(
        f"/api/v1/admin/users/{admin_id}/status",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_deact.status_code == 400
    assert "last active administrator" in res_deact.json()["detail"].lower()

    # Try demoting the only admin
    res_demote = client.patch(
        f"/api/v1/admin/users/{admin_id}/role",
        json={"role": "Viewer"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_demote.status_code == 400
    assert "last active administrator" in res_demote.json()["detail"].lower()


# ── SECURITY & PASSWORD HASHING TESTS ─────────────────────────────────────────

def test_password_hashing_security():
    """Test bcrypt password hashing and verification."""
    pw = "SuperSecurePassword123!"
    hashed = get_password_hash(pw)
    assert hashed.startswith("$2b$")
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_public_health_and_readiness_endpoints_open():
    """Test that /health and /ready remain public for monitoring without auth tokens."""
    res_health = client.get("/health")
    assert res_health.status_code == 200

    res_ready = client.get("/ready")
    assert res_ready.status_code in [200, 503]
