"""Test suite verifying Backend Tickets 502-507 (API endpoints, ML/Business integration & OpenAPI schema)."""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def get_auth_token(role: str = "Admin") -> str:
    """Utility helper to fetch a JWT token for testing."""
    role_email_map = {
        "Admin": ("admin@telecom.com", "AdminPassword123!"),
        "RetentionManager": ("manager@telecom.com", "ManagerPassword123!"),
        "Analyst": ("analyst@telecom.com", "AnalystPassword123!"),
        "ModelManager": ("modelmanager@telecom.com", "ModelPassword123!"),
        "Operations": ("operations@telecom.com", "OpsPassword123!"),
        "Viewer": ("viewer@telecom.com", "ViewerPassword123!"),
        "Executive": ("executive@telecom.com", "Password123!"),
    }
    email, password = role_email_map.get(role, (f"{role.lower()}@telecom.com", "Password123!"))
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, f"Login failed for role {role}: {response.text}"
    return response.json()["access_token"]



def test_ticket_502_customer_list():
    """TICKET-502: Test GET /api/v1/customers paginated response."""
    token = get_auth_token("RetentionManager")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/customers?page=1&page_size=10&sort_by=priority_score&sort_order=desc", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert len(data["items"]) <= 10
    if data["items"]:
        item = data["items"][0]
        assert "customer_id" in item
        assert "churn_probability" in item
        assert "priority_score" in item
        assert "recommended_action" in item


def test_ticket_503_customer_detail():
    """TICKET-503: Test GET /api/v1/customers/{id} full profile response."""
    token = get_auth_token("RetentionManager")
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch a valid customer_id from list
    list_res = client.get("/api/v1/customers?page=1&page_size=1", headers=headers)
    items = list_res.json()["items"]
    assert len(items) > 0
    cid = items[0]["customer_id"]

    response = client.get(f"/api/v1/customers/{cid}?reveal_pii=true", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["customer_id"] == cid
    assert "clv" in data
    assert "top_shap_features" in data
    assert "recommendation" in data
    assert "roi_details" in data["recommendation"]


def test_ticket_504_segments():
    """TICKET-504: Test GET /api/v1/segments cluster profiles & 2D scatter coordinates."""
    token = get_auth_token("Analyst")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/segments", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "segments" in data
    assert "scatter_points" in data
    assert len(data["segments"]) > 0


def test_ticket_505_model_metrics():
    """TICKET-505: Test GET /api/v1/models/metrics history & feature drift report."""
    token = get_auth_token("Analyst")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/models/metrics", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "current_model_version" in data
    assert "history" in data
    assert "drift_report" in data


def test_ticket_506_scoring_job_trigger():
    """TICKET-506: Test POST /api/v1/scoring-jobs trigger batch scoring."""
    token = get_auth_token("Admin")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"job_type": "BATCH_SCORING", "force_ingestion": True}
    response = client.post("/api/v1/scoring-jobs", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] in ["QUEUED", "RUNNING", "SUCCEEDED"]


def test_ticket_507_csv_export():
    """TICKET-507: Test GET /api/v1/export/customers CSV stream response."""
    token = get_auth_token("Admin")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/export/customers?risk_tier=High", headers=headers)
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "customer_id" in response.text
