"""Test Auth0 service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from auth0 import Auth0Error

from app.services.auth0_service import Auth0Service


class TestAuth0Service:
    """Test Auth0Service class."""

    @pytest.fixture
    def auth0_service(self):
        """Create Auth0Service instance."""
        with patch("app.services.auth0_service.get_settings") as mock_settings:
            mock_settings.return_value.AUTH0_DOMAIN = "test.auth0.com"
            mock_settings.return_value.AUTH0_CLIENT_ID = "client_id"
            mock_settings.return_value.AUTH0_CLIENT_SECRET = "secret"
            mock_settings.return_value.AUTH0_AUDIENCE = "audience"
            mock_settings.return_value.AUTH0_MANAGEMENT_CLIENT_ID = "mgmt_id"
            mock_settings.return_value.AUTH0_MANAGEMENT_CLIENT_SECRET = "mgmt_secret"
            return Auth0Service()

    @pytest.mark.asyncio
    async def test_register_user_success(self, auth0_service):
        """Test successful user registration."""
        with patch("app.services.auth0_service.GetToken") as mock_get_token, patch(
            "app.services.auth0_service.Auth0"
        ) as mock_auth0_class, patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_token = MagicMock()
            mock_token.client_credentials = MagicMock(return_value={"access_token": "mgmt_token"})
            mock_get_token.return_value = mock_token

            mock_management_api = MagicMock()
            mock_management_api.users.create = MagicMock(return_value={"user_id": "auth0_123"})
            mock_auth0_class.return_value = mock_management_api
            mock_to_thread.return_value = {"user_id": "auth0_123"}

            result = await auth0_service.register_user(
                email="test@example.com", password="password123", username="testuser"
            )

            assert "user_id" in result

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, auth0_service):
        """Test successful user retrieval by ID."""
        with patch("app.services.auth0_service.GetToken") as mock_get_token, patch(
            "app.services.auth0_service.Auth0"
        ) as mock_auth0_class, patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_token = MagicMock()
            mock_token.client_credentials = MagicMock(return_value={"access_token": "mgmt_token"})
            mock_get_token.return_value = mock_token

            mock_management_api = MagicMock()
            mock_management_api.users.get = MagicMock(return_value={"user_id": "auth0_123", "email": "test@example.com"})
            mock_auth0_class.return_value = mock_management_api
            mock_to_thread.return_value = {"user_id": "auth0_123", "email": "test@example.com"}

            result = await auth0_service.get_user_by_id("auth0_123")

            assert result is not None
            assert result["user_id"] == "auth0_123"

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, auth0_service):
        """Test user retrieval when not found."""
        with patch("app.services.auth0_service.GetToken") as mock_get_token, patch(
            "app.services.auth0_service.Auth0"
        ) as mock_auth0_class, patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_token = MagicMock()
            mock_token.client_credentials = MagicMock(return_value={"access_token": "mgmt_token"})
            mock_get_token.return_value = mock_token

            mock_management_api = MagicMock()
            mock_management_api.users.get = MagicMock(side_effect=Auth0Error(status_code=404, error_code="not_found", message="User not found"))
            mock_auth0_class.return_value = mock_management_api
            mock_to_thread.side_effect = Auth0Error(status_code=404, error_code="not_found", message="User not found")

            result = await auth0_service.get_user_by_id("invalid_id")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, auth0_service):
        """Test successful user retrieval by email."""
        with patch("app.services.auth0_service.GetToken") as mock_get_token, patch(
            "app.services.auth0_service.Auth0"
        ) as mock_auth0_class, patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_token = MagicMock()
            mock_token.client_credentials = MagicMock(return_value={"access_token": "mgmt_token"})
            mock_get_token.return_value = mock_token

            mock_management_api = MagicMock()
            mock_management_api.users_by_email.search_users_by_email = MagicMock(
                return_value=[{"user_id": "auth0_123", "email": "test@example.com"}]
            )
            mock_auth0_class.return_value = mock_management_api
            mock_to_thread.return_value = [{"user_id": "auth0_123", "email": "test@example.com"}]

            result = await auth0_service.get_user_by_email("test@example.com")

            assert result is not None
            assert result["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_authorization_url_success(self, auth0_service):
        """Test successful authorization URL generation."""
        url = auth0_service.get_authorization_url(
            provider="google", redirect_uri="https://app.com/callback", state="state123"
        )

        assert "https://" in url
        assert "google" in url.lower() or "authorize" in url.lower()

    @pytest.mark.asyncio
    async def test_exchange_code_for_tokens_success(self, auth0_service):
        """Test successful code exchange for tokens."""
        with patch("app.services.auth0_service.GetToken") as mock_get_token, patch(
            "asyncio.to_thread", new_callable=AsyncMock
        ) as mock_to_thread:
            mock_token = MagicMock()
            mock_token.authorization_code = MagicMock(
                return_value={"access_token": "token", "refresh_token": "refresh", "expires_in": 3600}
            )
            mock_get_token.return_value = mock_token
            mock_to_thread.return_value = {"access_token": "token", "refresh_token": "refresh", "expires_in": 3600}

            result = await auth0_service.exchange_code_for_tokens(code="auth_code", redirect_uri="https://app.com/callback")

            assert "access_token" in result

    @pytest.mark.asyncio
    async def test_get_userinfo_success(self, auth0_service):
        """Test successful userinfo retrieval."""
        with patch("app.services.auth0_service.GetToken") as mock_get_token, patch(
            "asyncio.to_thread", new_callable=AsyncMock
        ) as mock_to_thread:
            mock_token = MagicMock()
            mock_token.user_info = MagicMock(return_value={"sub": "auth0_123", "email": "test@example.com"})
            mock_get_token.return_value = mock_token
            mock_to_thread.return_value = {"sub": "auth0_123", "email": "test@example.com"}

            result = await auth0_service.get_userinfo("access_token")

            assert "sub" in result
            assert result["email"] == "test@example.com"

