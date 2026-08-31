"""Test suite verifying Epic 6 RBAC Matrix (03_Security_Access.md Section 4).

Validates exact HTTP 200 / 403 status code responses across Executive, RetentionManager, Analyst, and Admin roles.
"""

from fastapi.testclient import TestClient
import pytest
from backend.app.main import app

client = TestClient(app)


def get_token_for_role(role: str) -> str:
    """Helper to authenticate and retrieve a role-specific JWT bearer token."""
    role_credentials = {
        "Executive": ("executive@telecom.com", "Password123!"),
        "RetentionManager": ("manager@telecom.com", "ManagerPassword123!"),
        "Analyst": ("analyst@telecom.com", "AnalystPassword123!"),
        "Admin": ("admin@telecom.com", "AdminPassword123!"),
    }
    email, password = role_credentials[role]
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {role} ({email}): {res.status_code} {res.text}"
    return res.json()["access_token"]


@pytest.fixture(scope="module")
def first_customer_id():
    """Retrieve a valid customer ID for detail tests."""
    token = get_token_for_role("Admin")
    headers = {"Authorization": f"Bearer {token}"}
    res = client.get("/api/v1/customers?page=1&page_size=1", headers=headers)
    items = res.json()["items"]
    assert len(items) > 0
    return items[0]["customer_id"]


# Role matrix test cases: (role, endpoint_func_name, expected_status)
MATRIX_CASES = [
    # Customer List (GET /api/v1/customers)
    ("Executive", "get_customers", 200),
    ("RetentionManager", "get_customers", 200),
    ("Analyst", "get_customers", 200),
    ("Admin", "get_customers", 200),

    # Customer Detail Standard (GET /api/v1/customers/{id})
    ("Executive", "get_customer_detail_standard", 200),
    ("RetentionManager", "get_customer_detail_standard", 200),
    ("Analyst", "get_customer_detail_standard", 200),
    ("Admin", "get_customer_detail_standard", 200),

    # Customer Detail Reveal PII (GET /api/v1/customers/{id}?reveal_pii=true)
    ("Executive", "get_customer_detail_reveal_pii", 403),
    ("RetentionManager", "get_customer_detail_reveal_pii", 200),
    ("Analyst", "get_customer_detail_reveal_pii", 403),
    ("Admin", "get_customer_detail_reveal_pii", 200),

    # Retention Action Taken (POST /api/v1/customers/{id}/action)
    ("Executive", "post_customer_action", 403),
    ("RetentionManager", "post_customer_action", 200),
    ("Analyst", "post_customer_action", 403),
    ("Admin", "post_customer_action", 200),

    # Segments Overview (GET /api/v1/segments)
    ("Executive", "get_segments", 200),
    ("RetentionManager", "get_segments", 200),
    ("Analyst", "get_segments", 200),
    ("Admin", "get_segments", 200),

    # Model Monitoring Metrics (GET /api/v1/models/metrics)
    ("Executive", "get_model_metrics", 200),
    ("RetentionManager", "get_model_metrics", 200),
    ("Analyst", "get_model_metrics", 200),
    ("Admin", "get_model_metrics", 200),

    # Model Promotion (POST /api/v1/models/promote/v1788203728)
    ("Executive", "promote_model", 403),
    ("RetentionManager", "promote_model", 403),
    ("Analyst", "promote_model", 200),
    ("Admin", "promote_model", 200),

    # Trigger Scoring Job (POST /api/v1/scoring-jobs)
    ("Executive", "trigger_scoring_job", 403),
    ("RetentionManager", "trigger_scoring_job", 403),
    ("Analyst", "trigger_scoring_job", 200),
    ("Admin", "trigger_scoring_job", 200),

    # CSV Export (GET /api/v1/export/customers)
    ("Executive", "export_csv", 403),
    ("RetentionManager", "export_csv", 200),
    ("Analyst", "export_csv", 403),
    ("Admin", "export_csv", 200),

    # Audit Logs (GET /api/v1/admin/audit-logs)
    ("Executive", "get_audit_logs", 403),
    ("RetentionManager", "get_audit_logs", 403),
    ("Analyst", "get_audit_logs", 403),
    ("Admin", "get_audit_logs", 200),
]


@pytest.mark.parametrize("role,action_key,expected_status", MATRIX_CASES)
def test_rbac_permission_matrix(role, action_key, expected_status, first_customer_id):
    token = get_token_for_role(role)
    headers = {"Authorization": f"Bearer {token}"}
    cid = first_customer_id

    if action_key == "get_customers":
        res = client.get("/api/v1/customers?page=1&page_size=5", headers=headers)
    elif action_key == "get_customer_detail_standard":
        res = client.get(f"/api/v1/customers/{cid}", headers=headers)
    elif action_key == "get_customer_detail_reveal_pii":
        res = client.get(f"/api/v1/customers/{cid}?reveal_pii=true", headers=headers)
    elif action_key == "post_customer_action":
        res = client.post(f"/api/v1/customers/{cid}/action", headers=headers)
    elif action_key == "get_segments":
        res = client.get("/api/v1/segments", headers=headers)
    elif action_key == "get_model_metrics":
        res = client.get("/api/v1/models/metrics", headers=headers)
    elif action_key == "promote_model":
        res = client.post("/api/v1/models/promote/v1788203728", headers=headers)
    elif action_key == "trigger_scoring_job":
        res = client.post("/api/v1/scoring-jobs", json={"job_type": "BATCH_SCORING", "force_ingestion": False}, headers=headers)
    elif action_key == "export_csv":
        res = client.get("/api/v1/export/customers", headers=headers)
    elif action_key == "get_audit_logs":
        res = client.get("/api/v1/admin/audit-logs", headers=headers)
    else:
        raise ValueError(f"Unknown action_key: {action_key}")

    assert res.status_code == expected_status, f"Role '{role}' on action '{action_key}' expected HTTP {expected_status}, but got {res.status_code}: {res.text}"
