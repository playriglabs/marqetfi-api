"""Test security utilities."""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from unittest.mock import MagicMock

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_auth0_jwks,
    get_password_hash,
    verify_auth0_token,
    verify_password,
    verify_privy_token,
)


class TestSecurity:
    """Test security utilities."""

    def test_verify_password_success(self):
        """Test successful password verification."""
        password = "test_password"
        hashed = get_password_hash(password)

        result = verify_password(password, hashed)

        assert result is True

    def test_verify_password_failure(self):
        """Test password verification failure."""
        password = "test_password"
        hashed = get_password_hash(password)

        result = verify_password("wrong_password", hashed)

        assert result is False

    def test_get_password_hash(self):
        """Test password hashing."""
        password = "test_password"

        hashed = get_password_hash(password)

        assert hashed != password
        assert len(hashed) > 0

    def test_create_access_token(self):
        """Test creating access token."""
        data = {"sub": "user123", "email": "test@example.com"}

        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expires_delta(self):
        """Test creating access token with custom expiration."""
        data = {"sub": "user123"}
        expires_delta = timedelta(minutes=30)

        token = create_access_token(data, expires_delta=expires_delta)

        assert token is not None

    def test_create_refresh_token(self):
        """Test creating refresh token."""
        data = {"sub": "user123", "email": "test@example.com"}

        token = create_refresh_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token_with_expires_delta(self):
        """Test creating refresh token with custom expiration."""
        data = {"sub": "user123"}
        expires_delta = timedelta(days=7)

        token = create_refresh_token(data, expires_delta=expires_delta)

        assert token is not None

    def test_get_auth0_jwks_success(self):
        """Test successful Auth0 JWKS retrieval."""
        with patch("app.core.security.get_settings") as mock_settings, patch(
            "httpx.get"
        ) as mock_get:
            mock_settings.return_value.AUTH0_DOMAIN = "test.auth0.com"
            mock_response = MagicMock()
            mock_response.json.return_value = {"keys": []}
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            jwks = get_auth0_jwks()

            assert isinstance(jwks, dict)

    def test_get_auth0_jwks_no_domain(self):
        """Test Auth0 JWKS retrieval when domain not set."""
        with patch("app.core.security.get_settings") as mock_settings:
            mock_settings.return_value.AUTH0_DOMAIN = None

            jwks = get_auth0_jwks()

            assert jwks == {}

    def test_get_auth0_jwks_error(self):
        """Test Auth0 JWKS retrieval on error."""
        with patch("app.core.security.get_settings") as mock_settings, patch(
            "httpx.get", side_effect=Exception("Network error")
        ):
            mock_settings.return_value.AUTH0_DOMAIN = "test.auth0.com"

            jwks = get_auth0_jwks()

            assert jwks == {}

    def test_verify_auth0_token_success(self):
        """Test successful Auth0 token verification."""
        with patch("app.core.security.get_settings") as mock_settings, patch(
            "app.core.security.get_auth0_jwks", return_value={"keys": []}
        ), patch("jose.jwt.decode", return_value={"sub": "user123"}):
            mock_settings.return_value.AUTH0_DOMAIN = "test.auth0.com"
            mock_settings.return_value.AUTH0_AUDIENCE = "test_audience"

            payload = verify_auth0_token("valid_token")

            assert payload is not None
            assert payload["sub"] == "user123"

    def test_verify_auth0_token_no_domain(self):
        """Test Auth0 token verification when domain not set."""
        with patch("app.core.security.get_settings") as mock_settings:
            mock_settings.return_value.AUTH0_DOMAIN = None

            payload = verify_auth0_token("token")

            assert payload is None

    def test_verify_auth0_token_invalid(self):
        """Test Auth0 token verification with invalid token."""
        with patch("app.core.security.get_settings") as mock_settings, patch(
            "app.core.security.get_auth0_jwks", return_value={"keys": []}
        ), patch("jose.jwt.decode", side_effect=Exception("Invalid token")):
            mock_settings.return_value.AUTH0_DOMAIN = "test.auth0.com"
            mock_settings.return_value.AUTH0_AUDIENCE = "test_audience"

            payload = verify_auth0_token("invalid_token")

            assert payload is None

    @pytest.mark.asyncio
    async def test_verify_privy_token_success(self):
        """Test successful Privy token verification."""
        with patch("app.core.security.get_settings") as mock_settings, patch(
            "app.core.security.ProviderFactory"
        ) as mock_factory:
            mock_settings.return_value.PRIVY_APP_ID = "app_id"
            mock_settings.return_value.PRIVY_APP_SECRET = "secret"
            mock_provider = MagicMock()
            mock_provider.verify_access_token = AsyncMock(return_value={"sub": "user123"})
            mock_factory.get_auth_provider = AsyncMock(return_value=mock_provider)

            payload = await verify_privy_token("valid_token")

            assert payload is not None
            assert payload["sub"] == "user123"

    @pytest.mark.asyncio
    async def test_verify_privy_token_no_config(self):
        """Test Privy token verification when not configured."""
        with patch("app.core.security.get_settings") as mock_settings:
            mock_settings.return_value.PRIVY_APP_ID = None

            payload = await verify_privy_token("token")

            assert payload is None

    @pytest.mark.asyncio
    async def test_decode_token_auth0(self):
        """Test decoding Auth0 token."""
        with patch("app.core.security.get_settings") as mock_settings, patch(
            "app.core.security.verify_auth0_token", return_value={"sub": "user123"}
        ):
            mock_settings.return_value.AUTH0_DOMAIN = "test.auth0.com"

            payload = await decode_token("auth0_token")

            assert payload is not None
            assert payload["sub"] == "user123"

    @pytest.mark.asyncio
    async def test_decode_token_privy(self):
        """Test decoding Privy token."""
        with patch("app.core.security.get_settings") as mock_settings, patch(
            "app.core.security.verify_privy_token", return_value={"sub": "user123"}
        ):
            mock_settings.return_value.PRIVY_APP_ID = "app_id"
            mock_settings.return_value.AUTH0_DOMAIN = None

            payload = await decode_token("privy_token")

            assert payload is not None
            assert payload["sub"] == "user123"

    @pytest.mark.asyncio
    async def test_decode_token_custom(self):
        """Test decoding custom JWT token."""
        with patch("app.core.security.get_settings") as mock_settings, patch(
            "app.core.security.ProviderRegistry"
        ) as mock_registry, patch("jose.jwt.decode", return_value={"sub": "user123", "type": "access"}):
            mock_settings.return_value.AUTH0_DOMAIN = None
            mock_settings.return_value.PRIVY_APP_ID = None
            mock_settings.return_value.SECRET_KEY = "secret"
            mock_settings.return_value.ALGORITHM = "HS256"
            mock_registry.list_auth_providers = MagicMock(return_value=[])

            payload = await decode_token("custom_token")

            assert payload is not None
            assert payload["sub"] == "user123"

    @pytest.mark.asyncio
    async def test_decode_token_invalid(self):
        """Test decoding invalid token."""
        with patch("app.core.security.get_settings") as mock_settings, patch(
            "app.core.security.ProviderRegistry"
        ) as mock_registry, patch("jose.jwt.decode", side_effect=Exception("Invalid")):
            mock_settings.return_value.AUTH0_DOMAIN = None
            mock_settings.return_value.PRIVY_APP_ID = None
            mock_settings.return_value.SECRET_KEY = "secret"
            mock_settings.return_value.ALGORITHM = "HS256"
            mock_registry.list_auth_providers = MagicMock(return_value=[])

            payload = await decode_token("invalid_token")

            assert payload is None

