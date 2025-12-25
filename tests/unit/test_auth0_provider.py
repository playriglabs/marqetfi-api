"""Test Auth0AuthProvider."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.providers.auth0.config import Auth0AuthConfig
from app.services.providers.auth0.provider import Auth0AuthProvider


class TestAuth0AuthProvider:
    """Test Auth0AuthProvider class."""

    @pytest.fixture
    def auth0_config(self):
        """Create Auth0 config."""
        return Auth0AuthConfig(
            domain="test.auth0.com",
            client_id="client_id",
            client_secret="secret",
            audience="audience",
            management_client_id="mgmt_id",
            management_client_secret="mgmt_secret",
            algorithm="RS256",
        )

    @pytest.fixture
    def provider(self, auth0_config):
        """Create Auth0AuthProvider instance."""
        return Auth0AuthProvider(auth0_config)

    @pytest.mark.asyncio
    async def test_initialize_success(self, provider):
        """Test successful initialization."""
        await provider.initialize()
        assert provider._initialized is True

    @pytest.mark.asyncio
    async def test_initialize_missing_config(self):
        """Test initialization with missing config."""
        config = Auth0AuthConfig(
            domain="",
            client_id="",
            client_secret="",
            audience="",
            management_client_id="",
            management_client_secret="",
            algorithm="RS256",
        )
        provider = Auth0AuthProvider(config)

        with pytest.raises(ValueError, match="required"):
            await provider.initialize()

    @pytest.mark.asyncio
    async def test_health_check_success(self, provider):
        """Test successful health check."""
        await provider.initialize()

        with patch("app.services.providers.auth0.provider.GetToken") as mock_get_token:
            mock_token_instance = MagicMock()
            mock_token_instance.client_credentials = MagicMock(
                return_value={"access_token": "token"}
            )
            mock_get_token.return_value = mock_token_instance

            result = await provider.health_check()
            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self, provider):
        """Test health check when not initialized."""
        result = await provider.health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_failure(self, provider):
        """Test health check failure."""
        await provider.initialize()

        with patch("app.services.providers.auth0.provider.GetToken") as mock_get_token:
            mock_token_instance = MagicMock()
            mock_token_instance.client_credentials = MagicMock(side_effect=Exception("Error"))
            mock_get_token.return_value = mock_token_instance

            result = await provider.health_check()
            assert result is False

    @pytest.mark.asyncio
    async def test_verify_access_token_success(self, provider):
        """Test successful token verification."""
        with patch("app.services.providers.auth0.provider.verify_auth0_token") as mock_verify:
            mock_verify.return_value = {"sub": "user123", "email": "test@example.com"}

            result = await provider.verify_access_token("token")

            assert result is not None
            assert result["sub"] == "user123"
            mock_verify.assert_called_once_with("token")

    @pytest.mark.asyncio
    async def test_verify_access_token_invalid(self, provider):
        """Test invalid token verification."""
        with patch("app.services.providers.auth0.provider.verify_auth0_token") as mock_verify:
            mock_verify.return_value = None

            result = await provider.verify_access_token("invalid_token")

            assert result is None

    @pytest.mark.asyncio
    async def test_verify_access_token_missing_config(self):
        """Test token verification with missing config."""
        config = Auth0AuthConfig(
            domain="",
            client_id="",
            client_secret="",
            audience="",
            management_client_id="mgmt_id",
            management_client_secret="mgmt_secret",
            algorithm="RS256",
        )
        provider = Auth0AuthProvider(config)

        result = await provider.verify_access_token("token")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, provider):
        """Test getting user by ID."""
        await provider.initialize()

        mock_user = {"user_id": "auth0|123", "email": "test@example.com"}

        with patch.object(provider, "management_api") as mock_mgmt:
            mock_mgmt.users.get = MagicMock(return_value=mock_user)

            result = await provider.get_user_by_id("auth0|123")

            assert result is not None
            assert result["email"] == "test@example.com"
            # Access management_api property to trigger initialization
            _ = provider.management_api
            mock_mgmt.users.get.assert_called_once_with("auth0|123")

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, provider):
        """Test getting user by ID when not found."""
        await provider.initialize()

        with patch.object(provider, "management_api") as mock_mgmt:
            from auth0 import Auth0Error

            mock_mgmt.users.get = MagicMock(side_effect=Auth0Error(404, "Not found"))

            result = await provider.get_user_by_id("auth0|999")

            assert result is None
            # Access management_api property to trigger initialization
            _ = provider.management_api

    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, provider):
        """Test getting user by email."""
        await provider.initialize()

        mock_users = [{"user_id": "auth0|123", "email": "test@example.com"}]

        with patch.object(provider, "management_api") as mock_mgmt:
            mock_mgmt.users.list = MagicMock(return_value={"users": mock_users})

            result = await provider.get_user_by_email("test@example.com")

            assert result is not None
            assert result["user_id"] == "auth0|123"
            # Access management_api property to trigger initialization
            _ = provider.management_api

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, provider):
        """Test getting user by email when not found."""
        await provider.initialize()

        with patch.object(provider, "management_api") as mock_mgmt:
            mock_mgmt.users.list = MagicMock(return_value={"users": []})

            result = await provider.get_user_by_email("nonexistent@example.com")

            assert result is None
            # Access management_api property to trigger initialization
            _ = provider.management_api

    def test_extract_user_id_from_token(self, provider):
        """Test extracting user ID from token."""
        with patch("app.services.providers.auth0.provider.verify_auth0_token") as mock_verify:
            mock_verify.return_value = {"sub": "auth0|123"}

            result = provider.extract_user_id_from_token("token")

            assert result == "auth0|123"
            mock_verify.assert_called_once_with("token")

    @pytest.mark.asyncio
    async def test_management_api_property(self, provider):
        """Test management API property."""
        await provider.initialize()

        with patch("app.services.providers.auth0.provider.GetToken") as mock_get_token:
            mock_token_instance = MagicMock()
            mock_token_instance.client_credentials = MagicMock(
                return_value={"access_token": "mgmt_token"}
            )
            mock_get_token.return_value = mock_token_instance

            with patch("app.services.providers.auth0.provider.Auth0") as mock_auth0:
                mock_auth0_instance = MagicMock()
                mock_auth0.return_value = mock_auth0_instance

                api = provider.management_api

                assert api == mock_auth0_instance
                mock_auth0.assert_called_once_with(domain="test.auth0.com", token="mgmt_token")
