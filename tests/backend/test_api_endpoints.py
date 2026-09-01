"""Test FastAPI REST endpoints."""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_login_endpoint():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "manager@telecom.com", "password": "ManagerPassword123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "RetentionManager"


def test_customers_list_endpoint():
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "manager@telecom.com", "password": "ManagerPassword123!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    response = client.get(
        "/api/v1/customers?page=1&page_size=5",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) <= 5
    # Verify PII masking in list view
    if len(data["items"]) > 0:
        first_item = data["items"][0]
        assert "*" in first_item["name"] or first_item["name"] == "Customer"

