import pytest

from app import create_app
from database import db
from models import MenuItem, Order


@pytest.fixture
def client():
    app = create_app("testing")
    with app.app_context():
        yield app.test_client()


def get_auth_token(client, role="admin"):
    """Helper para obtener token según rol."""
    credentials = {
        "admin": {"username": "admin", "password": "admin123"},
        "cashier": {"username": "cajero1", "password": "cajero123"},
        "waiter": {"username": "mesero1", "password": "mesero123"},
    }
    
    creds = credentials.get(role, credentials["admin"])
    response = client.post("/api/auth/login", json=creds)
    data = response.get_json()
    return data["access_token"]


def test_login_admin(client):
    """Test login como admin."""
    response = client.post(
        "/api/auth/login", 
        json={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "access_token" in data
    assert data["user"]["role"] == "admin"


def test_login_cashier(client):
    """Test login como cajero."""
    response = client.post(
        "/api/auth/login",
        json={"username": "cajero1", "password": "cajero123"}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["user"]["role"] == "cashier"


def test_login_waiter(client):
    """Test login como mesero."""
    response = client.post(
        "/api/auth/login",
        json={"username": "mesero1", "password": "mesero123"}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["user"]["role"] == "waiter"


def test_get_menu_returns_200(client):
    """Test obtener menú sin autenticación."""
    response = client.get("/api/menu/")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_create_open_order_as_waiter(client):
    """Test crear ticket abierto como mesero."""
    token = get_auth_token(client, "waiter")
    
    with client.application.app_context():
        first_item = MenuItem.query.first()
    
    payload = {
        "customer_name": "Mesa 5",
        "order_type": "local",
        "items": [{"id": first_item.id, "quantity": 2}],
    }
    
    response = client.post(
        "/api/orders/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 201
    data = response.get_json()
    assert data["status"] == "open"
    assert data["customer_name"] == "Mesa 5"


def test_add_items_to_open_order(client):
    """Test agregar items a un ticket abierto."""
    token = get_auth_token(client, "waiter")
    
    with client.application.app_context():
        items = MenuItem.query.limit(2).all()
    
    # Crear orden abierta
    payload1 = {
        "customer_name": "Mesa 3",
        "items": [{"id": items[0].id, "quantity": 1}],
    }
    response1 = client.post(
        "/api/orders/",
        json=payload1,
        headers={"Authorization": f"Bearer {token}"},
    )
    order_id = response1.get_json()["id"]
    
    # Agregar más items
    payload2 = {
        "items": [{"id": items[1].id, "quantity": 2}],
    }
    response2 = client.post(
        f"/api/orders/{order_id}/items",
        json=payload2,
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response2.status_code == 200
    data = response2.get_json()
    assert len(data["items"]) == 2


def test_complete_order_as_cashier(client):
    """Test completar orden como cajero."""
    waiter_token = get_auth_token(client, "waiter")
    cashier_token = get_auth_token(client, "cashier")
    
    with client.application.app_context():
        first_item = MenuItem.query.first()
    
    # Mesero crea orden
    payload1 = {
        "customer_name": "Mesa 7",
        "items": [{"id": first_item.id, "quantity": 1}],
    }
    response1 = client.post(
        "/api/orders/",
        json=payload1,
        headers={"Authorization": f"Bearer {waiter_token}"},
    )
    order_id = response1.get_json()["id"]
    
    # Cajero completa orden
    payload2 = {"payment_method": "card"}
    response2 = client.put(
        f"/api/orders/{order_id}/complete",
        json=payload2,
        headers={"Authorization": f"Bearer {cashier_token}"},
    )
    
    assert response2.status_code == 200
    data = response2.get_json()
    assert data["status"] == "completed"


def test_waiter_cannot_complete_order(client):
    """Test que mesero no puede completar orden."""
    token = get_auth_token(client, "waiter")
    
    with client.application.app_context():
        first_item = MenuItem.query.first()
    
    # Crear orden
    payload1 = {
        "customer_name": "Mesa 1",
        "items": [{"id": first_item.id, "quantity": 1}],
    }
    response1 = client.post(
        "/api/orders/",
        json=payload1,
        headers={"Authorization": f"Bearer {token}"},
    )
    order_id = response1.get_json()["id"]
    
    # Intentar completar (debería fallar)
    response2 = client.put(
        f"/api/orders/{order_id}/complete",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response2.status_code == 403
