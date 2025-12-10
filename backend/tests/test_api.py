import pytest

from app import create_app
from database import db
from models import MenuItem


@pytest.fixture
def client():
    app = create_app("testing")
    with app.app_context():
        yield app.test_client()


def get_auth_token(client):
    response = client.post(
        "/api/auth/login", json={"username": "admin", "password": "admin123"}
    )
    data = response.get_json()
    return data["access_token"]


def test_get_menu_returns_200(client):
    response = client.get("/api/menu/")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_create_order(client):
    token = get_auth_token(client)
    with client.application.app_context():
        first_item = MenuItem.query.first()
    payload = {
        "customer_name": "Tester",
        "items": [{"id": first_item.id, "quantity": 1}],
        "payment_method": "cash",
    }
    response = client.post(
        "/api/orders/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["customer_name"] == "Tester"
    assert data["items"][0]["quantity"] == 1


def test_daily_report_without_sales(client):
    token = get_auth_token(client)
    response = client.get(
        "/api/reports/daily", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "total_orders" in data
