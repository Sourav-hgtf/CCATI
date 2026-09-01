from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.session import SessionLocal, engine
from backend.app.db.base import Base
from backend.scripts.seed_users import seed_database_users

client = TestClient(app)


def setup_function():
    Base.metadata.create_all(bind=engine)
    seed_database_users()


def _login(role: str):
    email_map = {
        "Admin": "admin@telecom.com",
        "RetentionManager": "manager@telecom.com",
        "Analyst": "analyst@telecom.com",
        "Viewer": "viewer@telecom.com",
    }
    password_map = {
        "Admin": "AdminPassword123!",
        "RetentionManager": "ManagerPassword123!",
        "Analyst": "AnalystPassword123!",
        "Viewer": "ViewerPassword123!",
    }
    payload = {"email": email_map[role], "password": password_map[role]}
    res = client.post("/api/v1/auth/login", json=payload)
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def test_customer_detail_response_masks_sensitive_fields_by_default():
    token = _login("Analyst")
    list_res = client.get("/api/v1/customers?page=1&page_size=5", headers={"Authorization": f"Bearer {token}"})
    assert list_res.status_code == 200, list_res.text
    customer_id = list_res.json()["items"][0]["customer_id"]

    detail_res = client.get(f"/api/v1/customers/{customer_id}", headers={"Authorization": f"Bearer {token}"})
    assert detail_res.status_code == 200, detail_res.text
    payload = detail_res.json()

    assert "name" in payload
    assert "customer_id" in payload
    assert "*" in payload["name"] or payload["name"] == "Customer"
    assert "*" in payload["phone"]
    assert "*" in payload["email"]
    assert payload["is_pii_revealed"] is False
    assert "password_hash" not in payload
    assert "access_token" not in payload
    assert "refresh_token" not in payload



def test_prediction_response_does_not_expose_internal_fields():
    token = _login("RetentionManager")
    list_res = client.get("/api/v1/customers?page=1&page_size=5", headers={"Authorization": f"Bearer {token}"})
    customer_id = list_res.json()["items"][0]["customer_id"]

    pred_res = client.post("/api/v1/predict", json={"customer_id": customer_id}, headers={"Authorization": f"Bearer {token}"})
    assert pred_res.status_code == 200, pred_res.text
    payload = pred_res.json()

    assert "customer_id" in payload
    assert "password_hash" not in payload
    assert "access_token" not in payload
    assert "refresh_token" not in payload
    assert "db_path" not in payload
    assert "model_path" not in payload


def test_customer_resource_access_depends_on_authenticated_user_permissions():
    analyst_token = _login("Analyst")
    admin_token = _login("Admin")

    list_res = client.get("/api/v1/customers?page=1&page_size=5", headers={"Authorization": f"Bearer {analyst_token}"})
    customer_id = list_res.json()["items"][0]["customer_id"]

    detail_res = client.get(f"/api/v1/customers/{customer_id}?reveal_pii=true", headers={"Authorization": f"Bearer {analyst_token}"})
    assert detail_res.status_code == 403

    admin_res = client.get(f"/api/v1/customers/{customer_id}?reveal_pii=true", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_res.status_code in (200, 404)
