"""Integration tests for webhook API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

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
def authenticated_client(client: TestClient, test_user: User) -> TestClient:
    """Create authenticated test client with dependency override."""
    from app.api.dependencies import get_current_active_user
    from app.main import app

    def override_get_current_user():
        return test_user

    app.dependency_overrides[get_current_active_user] = override_get_current_user
    yield client
    app.dependency_overrides.clear()


def test_create_webhook(authenticated_client: TestClient):
    """Test creating a new webhook configuration."""
    webhook_data = {
        "url": "https://example.com/webhook",
        "secret": "test_secret_key_123456",
        "event_types": ["trade.executed", "position.updated"],
    }

    response = authenticated_client.post("/api/v1/webhooks/", json=webhook_data)

    assert response.status_code == 201
    data = response.json()
    assert data["url"] == webhook_data["url"]
    assert data["event_types"] == webhook_data["event_types"]
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data


def test_create_webhook_unauthorized(client: TestClient):
    """Test creating webhook without authentication fails."""
    from app.main import app

    app.dependency_overrides.clear()

    webhook_data = {
        "url": "https://example.com/webhook",
        "secret": "test_secret_key_123456",
        "event_types": ["trade.executed"],
    }

    response = client.post("/api/v1/webhooks/", json=webhook_data)
    assert response.status_code == 403


def test_create_webhook_invalid_url(authenticated_client: TestClient):
    """Test creating webhook with invalid URL fails."""
    webhook_data = {
        "url": "not-a-valid-url",
        "secret": "test_secret_key_123456",
        "event_types": ["trade.executed"],
    }

    response = authenticated_client.post("/api/v1/webhooks/", json=webhook_data)
    assert response.status_code == 422


def test_create_webhook_short_secret(authenticated_client: TestClient):
    """Test creating webhook with short secret fails."""
    webhook_data = {
        "url": "https://example.com/webhook",
        "secret": "short",
        "event_types": ["trade.executed"],
    }

    response = authenticated_client.post("/api/v1/webhooks/", json=webhook_data)
    assert response.status_code == 422


def test_list_webhooks(authenticated_client: TestClient):
    """Test listing user's webhooks."""
    webhook_data = {
        "url": "https://example.com/webhook1",
        "secret": "test_secret_key_123456",
        "event_types": ["trade.executed"],
    }
    authenticated_client.post("/api/v1/webhooks/", json=webhook_data)

    webhook_data["url"] = "https://example.com/webhook2"
    authenticated_client.post("/api/v1/webhooks/", json=webhook_data)

    response = authenticated_client.get("/api/v1/webhooks/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


def test_get_webhook(authenticated_client: TestClient):
    """Test getting a specific webhook by ID."""
    webhook_data = {
        "url": "https://example.com/webhook",
        "secret": "test_secret_key_123456",
        "event_types": ["trade.executed"],
    }
    create_response = authenticated_client.post("/api/v1/webhooks/", json=webhook_data)
    webhook_id = create_response.json()["id"]

    response = authenticated_client.get(f"/api/v1/webhooks/{webhook_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == webhook_id
    assert data["url"] == webhook_data["url"]


def test_get_webhook_not_found(authenticated_client: TestClient):
    """Test getting non-existent webhook returns 404."""
    response = authenticated_client.get("/api/v1/webhooks/99999")
    assert response.status_code == 404


def test_update_webhook(authenticated_client: TestClient):
    """Test updating a webhook configuration."""
    webhook_data = {
        "url": "https://example.com/webhook",
        "secret": "test_secret_key_123456",
        "event_types": ["trade.executed"],
    }
    create_response = authenticated_client.post("/api/v1/webhooks/", json=webhook_data)
    webhook_id = create_response.json()["id"]

    update_data = {
        "url": "https://example.com/webhook-updated",
        "event_types": ["trade.executed", "order.filled"],
    }
    response = authenticated_client.put(f"/api/v1/webhooks/{webhook_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["url"] == update_data["url"]
    assert data["event_types"] == update_data["event_types"]


def test_update_webhook_partial(authenticated_client: TestClient):
    """Test partial update of webhook."""
    webhook_data = {
        "url": "https://example.com/webhook",
        "secret": "test_secret_key_123456",
        "event_types": ["trade.executed"],
    }
    create_response = authenticated_client.post("/api/v1/webhooks/", json=webhook_data)
    webhook_id = create_response.json()["id"]

    update_data = {"is_active": False}
    response = authenticated_client.put(f"/api/v1/webhooks/{webhook_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False
    assert data["url"] == webhook_data["url"]


def test_delete_webhook(authenticated_client: TestClient):
    """Test deleting a webhook configuration."""
    webhook_data = {
        "url": "https://example.com/webhook",
        "secret": "test_secret_key_123456",
        "event_types": ["trade.executed"],
    }
    create_response = authenticated_client.post("/api/v1/webhooks/", json=webhook_data)
    webhook_id = create_response.json()["id"]

    response = authenticated_client.delete(f"/api/v1/webhooks/{webhook_id}")
    assert response.status_code == 204

    get_response = authenticated_client.get(f"/api/v1/webhooks/{webhook_id}")
    assert get_response.status_code == 404


def test_enable_webhook(authenticated_client: TestClient):
    """Test enabling a disabled webhook."""
    webhook_data = {
        "url": "https://example.com/webhook",
        "secret": "test_secret_key_123456",
        "event_types": ["trade.executed"],
    }
    create_response = authenticated_client.post("/api/v1/webhooks/", json=webhook_data)
    webhook_id = create_response.json()["id"]

    authenticated_client.put(f"/api/v1/webhooks/{webhook_id}", json={"is_active": False})

    response = authenticated_client.put(f"/api/v1/webhooks/{webhook_id}/enable")

    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is True


def test_get_webhook_deliveries(authenticated_client: TestClient):
    """Test getting delivery history for a webhook."""
    webhook_data = {
        "url": "https://example.com/webhook",
        "secret": "test_secret_key_123456",
        "event_types": ["trade.executed"],
    }
    create_response = authenticated_client.post("/api/v1/webhooks/", json=webhook_data)
    webhook_id = create_response.json()["id"]

    response = authenticated_client.get(f"/api/v1/webhooks/{webhook_id}/deliveries")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


async def test_webhook_isolation_between_users(
    authenticated_client: TestClient, client: TestClient, db_session: AsyncSession
):
    """Test that users cannot access other users' webhooks."""
    webhook_data = {
        "url": "https://example.com/webhook",
        "secret": "test_secret_key_123456",
        "event_types": ["trade.executed"],
    }
    create_response = authenticated_client.post("/api/v1/webhooks/", json=webhook_data)
    webhook_id = create_response.json()["id"]

    from app.api.dependencies import get_current_active_user
    from app.main import app
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
    await db_session.refresh(other_user)

    def override_get_other_user():
        return other_user

    app.dependency_overrides[get_current_active_user] = override_get_other_user

    response = client.get(f"/api/v1/webhooks/{webhook_id}")
    assert response.status_code == 403

    app.dependency_overrides.clear()
