"""Integration tests for webhook API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import User


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    from app.repositories.user_repository import UserRepository

    repo = UserRepository()
    user = await repo.create(
        db_session,
        {
            "email": "webhook-test@example.com",
            "username": "webhook_test_user",
            "hashed_password": "test_hash",
            "is_active": True,
        },
    )
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    """Create authentication headers for test user."""
    token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


def test_create_webhook(client: TestClient, auth_headers: dict[str, str]):
    """Test creating a new webhook configuration."""
    webhook_data = {
        "url": "https://example.com/webhook",
        "secret": "test_secret_key_123456",
        "event_types": ["trade.executed", "position.updated"],
    }

    response = client.post("/api/v1/webhooks/", json=webhook_data, headers=auth_headers)

    assert response.status_code == 201
    data = response.json()
    assert data["url"] == webhook_data["url"]
    assert data["event_types"] == webhook_data["event_types"]
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data


def test_create_webhook_unauthorized(client: TestClient):
    """Test creating webhook without authentication fails."""
    webhook_data = {
        "url": "https://example.com/webhook",
        "secret": "test_secret_key_123456",
        "event_types": ["trade.executed"],
    }

    response = client.post("/api/v1/webhooks/", json=webhook_data)
    assert response.status_code == 401


def test_create_webhook_invalid_url(client: TestClient, auth_headers: dict[str, str]):
    """Test creating webhook with invalid URL fails."""
    webhook_data = {
        "url": "not-a-valid-url",
        "secret": "test_secret_key_123456",
        "event_types": ["trade.executed"],
    }

    response = client.post("/api/v1/webhooks/", json=webhook_data, headers=auth_headers)
    assert response.status_code == 422


def test_create_webhook_short_secret(client: TestClient, auth_headers: dict[str, str]):
    """Test creating webhook with short secret fails."""
    webhook_data = {
        "url": "https://example.com/webhook",
        "secret": "short",
        "event_types": ["trade.executed"],
    }

    response = client.post("/api/v1/webhooks/", json=webhook_data, headers=auth_headers)
    assert response.status_code == 422


def test_list_webhooks(client: TestClient, auth_headers: dict[str, str]):
    """Test listing user's webhooks."""
    webhook_data = {
        "url": "https://example.com/webhook1",
        "secret": "test_secret_key_123456",
        "event_types": ["trade.executed"],
    }
    client.post("/api/v1/webhooks/", json=webhook_data, headers=auth_headers)

    webhook_data["url"] = "https://example.com/webhook2"
    client.post("/api/v1/webhooks/", json=webhook_data, headers=auth_headers)

    response = client.get("/api/v1/webhooks/", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


def test_get_webhook(client: TestClient, auth_headers: dict[str, str]):
    """Test getting a specific webhook by ID."""
    webhook_data = {
        "url": "https://example.com/webhook",
        "secret": "test_secret_key_123456",
        "event_types": ["trade.executed"],
    }
    create_response = client.post("/api/v1/webhooks/", json=webhook_data, headers=auth_headers)
    webhook_id = create_response.json()["id"]

    response = client.get(f"/api/v1/webhooks/{webhook_id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == webhook_id
    assert data["url"] == webhook_data["url"]


def test_get_webhook_not_found(client: TestClient, auth_headers: dict[str, str]):
    """Test getting non-existent webhook returns 404."""
    response = client.get("/api/v1/webhooks/99999", headers=auth_headers)
    assert response.status_code == 404


def test_update_webhook(client: TestClient, auth_headers: dict[str, str]):
    """Test updating a webhook configuration."""
    webhook_data = {
        "url": "https://example.com/webhook",
        "secret": "test_secret_key_123456",
        "event_types": ["trade.executed"],
    }
    create_response = client.post("/api/v1/webhooks/", json=webhook_data, headers=auth_headers)
    webhook_id = create_response.json()["id"]

    update_data = {
        "url": "https://example.com/webhook-updated",
        "event_types": ["trade.executed", "order.filled"],
    }
    response = client.put(f"/api/v1/webhooks/{webhook_id}", json=update_data, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["url"] == update_data["url"]
    assert data["event_types"] == update_data["event_types"]


def test_update_webhook_partial(client: TestClient, auth_headers: dict[str, str]):
    """Test partial update of webhook."""
    webhook_data = {
        "url": "https://example.com/webhook",
        "secret": "test_secret_key_123456",
        "event_types": ["trade.executed"],
    }
    create_response = client.post("/api/v1/webhooks/", json=webhook_data, headers=auth_headers)
    webhook_id = create_response.json()["id"]

    update_data = {"is_active": False}
    response = client.put(f"/api/v1/webhooks/{webhook_id}", json=update_data, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False
    assert data["url"] == webhook_data["url"]


def test_delete_webhook(client: TestClient, auth_headers: dict[str, str]):
    """Test deleting a webhook configuration."""
    webhook_data = {
        "url": "https://example.com/webhook",
        "secret": "test_secret_key_123456",
        "event_types": ["trade.executed"],
    }
    create_response = client.post("/api/v1/webhooks/", json=webhook_data, headers=auth_headers)
    webhook_id = create_response.json()["id"]

    response = client.delete(f"/api/v1/webhooks/{webhook_id}", headers=auth_headers)
    assert response.status_code == 204

    get_response = client.get(f"/api/v1/webhooks/{webhook_id}", headers=auth_headers)
    assert get_response.status_code == 404


def test_enable_webhook(client: TestClient, auth_headers: dict[str, str]):
    """Test enabling a disabled webhook."""
    webhook_data = {
        "url": "https://example.com/webhook",
        "secret": "test_secret_key_123456",
        "event_types": ["trade.executed"],
    }
    create_response = client.post("/api/v1/webhooks/", json=webhook_data, headers=auth_headers)
    webhook_id = create_response.json()["id"]

    client.put(f"/api/v1/webhooks/{webhook_id}", json={"is_active": False}, headers=auth_headers)

    response = client.put(f"/api/v1/webhooks/{webhook_id}/enable", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is True


def test_get_webhook_deliveries(client: TestClient, auth_headers: dict[str, str]):
    """Test getting delivery history for a webhook."""
    webhook_data = {
        "url": "https://example.com/webhook",
        "secret": "test_secret_key_123456",
        "event_types": ["trade.executed"],
    }
    create_response = client.post("/api/v1/webhooks/", json=webhook_data, headers=auth_headers)
    webhook_id = create_response.json()["id"]

    response = client.get(f"/api/v1/webhooks/{webhook_id}/deliveries", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


async def test_webhook_isolation_between_users(
    client: TestClient, auth_headers: dict[str, str], db_session: AsyncSession
):
    """Test that users cannot access other users' webhooks."""
    webhook_data = {
        "url": "https://example.com/webhook",
        "secret": "test_secret_key_123456",
        "event_types": ["trade.executed"],
    }
    create_response = client.post("/api/v1/webhooks/", json=webhook_data, headers=auth_headers)
    webhook_id = create_response.json()["id"]

    from app.repositories.user_repository import UserRepository

    repo = UserRepository()
    other_user = await repo.create(
        db_session,
        {
            "email": "other-user@example.com",
            "username": "other_user",
            "hashed_password": "test_hash",
            "is_active": True,
        },
    )
    await db_session.commit()

    other_token = create_access_token({"sub": str(other_user.id)})
    other_headers = {"Authorization": f"Bearer {other_token}"}

    response = client.get(f"/api/v1/webhooks/{webhook_id}", headers=other_headers)
    assert response.status_code == 403
