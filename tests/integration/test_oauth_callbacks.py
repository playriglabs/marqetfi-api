"""Integration tests for OAuth callback endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.models.enums import AuthMethod
from app.models.user import User


@pytest.mark.asyncio
async def test_oauth_authorize_google(client: TestClient):
    """Test OAuth authorization for Google."""
    with patch("app.services.oauth_service.OAuthService.get_oauth_authorization_url") as mock_auth:
        mock_auth.return_value = (
            "https://auth0.example.com/authorize?client_id=123&connection=google-oauth2&state=abc123",
            "abc123",
        )

        response = client.get("/api/v1/auth/oauth/authorize/google")

        assert response.status_code == 200
        data = response.json()
        assert "authorization_url" in data
        assert "state" in data
        assert data["state"] == "abc123"


@pytest.mark.asyncio
async def test_oauth_authorize_apple(client: TestClient):
    """Test OAuth authorization for Apple."""
    with patch("app.services.oauth_service.OAuthService.get_oauth_authorization_url") as mock_auth:
        mock_auth.return_value = (
            "https://auth0.example.com/authorize?client_id=123&connection=apple&state=xyz789",
            "xyz789",
        )

        response = client.get("/api/v1/auth/oauth/authorize/apple")

        assert response.status_code == 200
        data = response.json()
        assert "authorization_url" in data
        assert "state" in data


@pytest.mark.asyncio
async def test_oauth_callback_google_success(client: TestClient):
    """Test Google OAuth callback success."""
    mock_user = MagicMock(spec=User)
    mock_user.id = 1
    mock_user.email = "test@example.com"
    mock_user.auth_method = AuthMethod.GOOGLE

    tokens = {
        "access_token": "jwt_token_123",
        "refresh_token": "refresh_token_123",
        "token_type": "bearer",
    }

    with patch("app.services.oauth_service.OAuthService.handle_oauth_callback") as mock_callback:
        mock_callback.return_value = (mock_user, tokens)

        response = client.get(
            "/api/v1/auth/oauth/google/callback?code=auth_code_123&state=valid_state"
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["access_token"] == "jwt_token_123"


@pytest.mark.asyncio
async def test_oauth_callback_apple_success(client: TestClient):
    """Test Apple OAuth callback success."""
    mock_user = MagicMock(spec=User)
    mock_user.id = 1
    mock_user.email = "test@example.com"
    mock_user.auth_method = AuthMethod.APPLE

    tokens = {
        "access_token": "jwt_token_456",
        "refresh_token": "refresh_token_456",
        "token_type": "bearer",
    }

    with patch("app.services.oauth_service.OAuthService.handle_oauth_callback") as mock_callback:
        mock_callback.return_value = (mock_user, tokens)

        response = client.get(
            "/api/v1/auth/oauth/apple/callback?code=auth_code_456&state=valid_state"
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["access_token"] == "jwt_token_456"


@pytest.mark.asyncio
async def test_oauth_callback_invalid_state(client: TestClient):
    """Test OAuth callback with invalid state."""
    with patch("app.services.oauth_service.OAuthService.handle_oauth_callback") as mock_callback:
        mock_callback.side_effect = ValueError("OAuth state validation failed: Invalid or expired OAuth state")

        response = client.get(
            "/api/v1/auth/oauth/google/callback?code=auth_code_123&state=invalid_state"
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "state" in data["detail"].lower() or "invalid" in data["detail"].lower()


@pytest.mark.asyncio
async def test_oauth_callback_token_exchange_failure(client: TestClient):
    """Test OAuth callback with token exchange failure."""
    with patch("app.services.oauth_service.OAuthService.handle_oauth_callback") as mock_callback:
        mock_callback.side_effect = ValueError("OAuth token exchange failed: Invalid code")

        response = client.get(
            "/api/v1/auth/oauth/google/callback?code=invalid_code&state=valid_state"
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "token" in data["detail"].lower() or "exchange" in data["detail"].lower()


@pytest.mark.asyncio
async def test_oauth_callback_missing_code(client: TestClient):
    """Test OAuth callback with missing code parameter."""
    response = client.get("/api/v1/auth/oauth/google/callback?state=valid_state")

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_oauth_callback_missing_state(client: TestClient):
    """Test OAuth callback with missing state parameter."""
    response = client.get("/api/v1/auth/oauth/google/callback?code=auth_code_123")

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_oauth_callback_generic_endpoint(client: TestClient):
    """Test generic OAuth callback endpoint."""
    mock_user = MagicMock(spec=User)
    mock_user.id = 1
    mock_user.email = "test@example.com"

    tokens = {
        "access_token": "jwt_token_generic",
        "refresh_token": "refresh_token_generic",
        "token_type": "bearer",
    }

    with patch("app.services.oauth_service.OAuthService.handle_oauth_callback") as mock_callback:
        mock_callback.return_value = (mock_user, tokens)

        response = client.get(
            "/api/v1/auth/oauth/callback?code=auth_code_123&state=valid_state"
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

