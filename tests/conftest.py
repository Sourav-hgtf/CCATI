"""Global Pytest Configuration and Fixtures for CCATI Test Suite."""

import pytest
from backend.app.db.base import Base
from backend.app.db.session import engine
from backend.app.core.rate_limiter import _default_store
from backend.app.core.security import create_access_token
from backend.scripts.seed_users import seed_database_users


@pytest.fixture(scope="session", autouse=True)
def initialize_test_database():
    """Ensure database tables and seed users are initialized before test execution."""
    Base.metadata.create_all(bind=engine)
    seed_database_users()


@pytest.fixture(autouse=True)
def reset_rate_limit_counters():
    """Reset rate limiter counters before and after each test."""
    _default_store.reset()
    yield
    _default_store.reset()



@pytest.fixture
def admin_headers():
    """Return Authorization headers for Admin user."""
    token = create_access_token(
        subject={"sub": "usr-admin-001", "email": "admin@telecom.com", "role": "Admin"}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def analyst_headers():
    """Return Authorization headers for Analyst user."""
    token = create_access_token(
        subject={"sub": "usr-analyst-003", "email": "analyst@telecom.com", "role": "Analyst"}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def manager_headers():
    """Return Authorization headers for RetentionManager user."""
    token = create_access_token(
        subject={"sub": "usr-retention-002", "email": "manager@telecom.com", "role": "RetentionManager"}
    )
    return {"Authorization": f"Bearer {token}"}
