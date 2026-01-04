"""Test PrivyAuthProvider."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.providers.privy.config import PrivyAuthConfig
from app.services.providers.privy.provider import PrivyAuthProvider


class TestPrivyAuthProvider:
    """Test PrivyAuthProvider class."""

    @pytest.fixture
    def privy_config(self):
        """Create Privy config."""
        return PrivyAuthConfig(
            enabled=True,
            app_id="test_app_id",
            app_secret="test_secret",
            environment="production",
            timeout=30,
            retry_attempts=3,
            retry_delay=1.0,
        )

    @pytest.fixture
    def provider(self, privy_config):
        """Create PrivyAuthProvider instance."""
        return PrivyAuthProvider(privy_config)

    @pytest.mark.asyncio
    async def test_initialize_success(self, provider):
        """Test successful initialization."""
        with patch("app.services.providers.privy.provider.AsyncPrivyAPI") as mock_privy:
            mock_client = MagicMock()
            mock_privy.return_value = mock_client

            await provider.initialize()

            assert provider._initialized is True
            # AsyncPrivyAPI should be called when _get_client is called
            await provider._get_client()
            mock_privy.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_success(self, provider):
        """Test successful health check."""
        await provider.initialize()

        # The health_check method checks _initialized and _client
        # Since _client is None initially (created lazily), we need to set it
        # or ensure _get_client returns a client
        with patch.object(provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            # Also set _client so the initial check passes
            provider._client = mock_client

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

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_get_client.side_effect = Exception("Error")

            result = await provider.health_check()

            assert result is False

    @pytest.mark.asyncio
    async def test_verify_access_token_success(self, provider):
        """Test successful token verification."""
        await provider.initialize()

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.auth.verify_access_token = AsyncMock(return_value={"sub": "user123"})
            mock_get_client.return_value = mock_client

            result = await provider.verify_access_token("token")

            assert result is not None
            assert result["sub"] == "user123"

    @pytest.mark.asyncio
    async def test_verify_access_token_invalid(self, provider):
        """Test invalid token verification."""
        await provider.initialize()

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            # AuthenticationError likely inherits from APIStatusError and needs args
            mock_client.auth.verify_access_token = AsyncMock(side_effect=Exception("Invalid"))
            mock_get_client.return_value = mock_client

            result = await provider.verify_access_token("invalid_token")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, provider):
        """Test getting user by ID."""
        await provider.initialize()

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.users.get = AsyncMock(
                return_value={"id": "user123", "email": "test@example.com"}
            )
            mock_get_client.return_value = mock_client

            result = await provider.get_user_by_id("user123")

            assert result is not None
            assert result["id"] == "user123"

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, provider):
        """Test getting user by ID when not found."""
        await provider.initialize()

        with patch.object(provider, "_get_client") as mock_get_client:
            from app.services.providers.privy.provider import APIStatusError

            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_error = APIStatusError("Not found", response=mock_response, body={})
            mock_client.users.get = AsyncMock(side_effect=mock_error)
            mock_get_client.return_value = mock_client

            result = await provider.get_user_by_id("nonexistent")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, provider):
        """Test getting user by email."""
        await provider.initialize()

        with patch.object(provider, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            # Mock users.list() to return a list with the user
            mock_user = MagicMock()
            mock_user.to_dict = MagicMock(
                return_value={"id": "user123", "email": "test@example.com"}
            )
            mock_users_response = MagicMock()
            mock_users_response.to_dict = MagicMock(return_value={"users": [mock_user]})
            mock_client.users.list = AsyncMock(return_value=mock_users_response)
            mock_get_client.return_value = mock_client

            result = await provider.get_user_by_email("test@example.com")

            assert result is not None
            assert result["id"] == "user123"
            assert result["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, provider):
        """Test getting user by email when not found."""
        await provider.initialize()

        with patch.object(provider, "_get_client") as mock_get_client:
            from app.services.providers.privy.provider import APIStatusError

            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_error = APIStatusError("Not found", response=mock_response, body={})
            mock_client.users.get_by_email = AsyncMock(side_effect=mock_error)
            mock_get_client.return_value = mock_client

            result = await provider.get_user_by_email("nonexistent@example.com")

            assert result is None

    def test_extract_user_id_from_token(self, provider):
        """Test extracting user ID from token."""
        token_payload = {"sub": "user123", "email": "test@example.com"}

        result = provider.extract_user_id_from_token(token_payload)

        assert result == "user123"

    def test_extract_user_id_from_token_user_id(self, provider):
        """Test extracting user ID from user_id field."""
        token_payload = {"user_id": "user123", "email": "test@example.com"}

        result = provider.extract_user_id_from_token(token_payload)

        assert result == "user123"

    def test_extract_user_id_from_token_no_sub(self, provider):
        """Test extracting user ID when sub is missing."""
        token_payload = {"email": "test@example.com"}

        result = provider.extract_user_id_from_token(token_payload)

        assert result is None
