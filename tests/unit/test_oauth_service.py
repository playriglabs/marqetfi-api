"""Test OAuth service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.user import User
from app.services.oauth_service import OAuthService


class TestOAuthService:
    """Test OAuthService class."""

    @pytest.fixture
    def oauth_service(self):
        """Create OAuthService instance."""
        return OAuthService()

    @pytest.fixture
    def sample_user(self):
        """Create sample user."""
        return User(
            id=1,
            email="test@example.com",
            username="testuser",
            is_active=True,
        )

    @pytest.mark.asyncio
    async def test_get_oauth_authorization_url_google(self, oauth_service):
        """Test getting Google OAuth authorization URL."""
        with patch("app.services.oauth_service.cache_manager") as mock_cache, patch.object(
            oauth_service.auth0_service, "get_authorization_url", return_value="https://auth0.com/auth"
        ), patch("app.services.oauth_service.get_settings") as mock_settings:
            mock_settings.return_value.AUTH0_GOOGLE_ENABLED = True
            mock_settings.return_value.AUTH0_OAUTH_REDIRECT_URI = "https://app.com/callback"
            mock_cache.set = AsyncMock()

            url, state = await oauth_service.get_oauth_authorization_url("google")

            assert url == "https://auth0.com/auth"
            assert state is not None
            mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_oauth_authorization_url_apple(self, oauth_service):
        """Test getting Apple OAuth authorization URL."""
        with patch("app.services.oauth_service.cache_manager") as mock_cache, patch.object(
            oauth_service.auth0_service, "get_authorization_url", return_value="https://auth0.com/auth"
        ), patch("app.services.oauth_service.get_settings") as mock_settings:
            mock_settings.return_value.AUTH0_APPLE_ENABLED = True
            mock_settings.return_value.AUTH0_OAUTH_REDIRECT_URI = "https://app.com/callback"
            mock_cache.set = AsyncMock()

            url, state = await oauth_service.get_oauth_authorization_url("apple")

            assert url == "https://auth0.com/auth"
            assert state is not None

    @pytest.mark.asyncio
    async def test_get_oauth_authorization_url_unsupported(self, oauth_service):
        """Test getting OAuth URL for unsupported provider."""
        with pytest.raises(ValueError, match="Unsupported OAuth provider"):
            await oauth_service.get_oauth_authorization_url("github")

    @pytest.mark.asyncio
    async def test_handle_oauth_callback_success(self, oauth_service, db_session, sample_user):
        """Test successful OAuth callback handling."""
        with patch("app.services.oauth_service.cache_manager") as mock_cache, patch.object(
            oauth_service.auth0_service, "exchange_code_for_tokens", return_value={"access_token": "token"}
        ), patch.object(
            oauth_service.auth0_service, "get_userinfo", return_value={"sub": "google-oauth2|123"}
        ), patch.object(
            oauth_service.auth_service, "create_or_update_user_from_auth0", return_value=sample_user
        ), patch.object(
            oauth_service.auth_service, "_store_oauth_connection", new_callable=AsyncMock
        ), patch.object(
            oauth_service.auth_service, "_generate_tokens", return_value={"access_token": "token"}
        ):
            mock_cache.get = AsyncMock(
                return_value={"provider": "google", "redirect_uri": "https://app.com/callback"}
            )
            mock_cache.delete = AsyncMock()

            user, tokens = await oauth_service.handle_oauth_callback(
                db=db_session, code="auth_code", state="state_token"
            )

            assert user.id == 1
            assert "access_token" in tokens

    @pytest.mark.asyncio
    async def test_handle_oauth_callback_invalid_state(self, oauth_service, db_session):
        """Test OAuth callback with invalid state."""
        with patch("app.services.oauth_service.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)

            with pytest.raises(ValueError, match="OAuth state validation failed"):
                await oauth_service.handle_oauth_callback(
                    db=db_session, code="auth_code", state="invalid_state"
                )

    @pytest.mark.asyncio
    async def test_link_oauth_account_success(self, oauth_service, db_session, sample_user):
        """Test successfully linking OAuth account."""
        with patch.object(
            oauth_service.auth0_service, "exchange_code_for_tokens", return_value={"access_token": "token"}
        ), patch.object(
            oauth_service.auth0_service, "get_userinfo", return_value={"sub": "google-oauth2|123"}
        ), patch.object(
            oauth_service.auth_service, "_store_oauth_connection", return_value=MagicMock()
        ), patch("app.services.oauth_service.get_settings") as mock_settings:
            mock_settings.return_value.AUTH0_OAUTH_REDIRECT_URI = "https://app.com/callback"

            result = await oauth_service.link_oauth_account(
                db=db_session, user=sample_user, code="auth_code"
            )

            assert result is not None

    @pytest.mark.asyncio
    async def test_unlink_oauth_account_success(self, oauth_service, db_session, sample_user):
        """Test successfully unlinking OAuth account."""
        mock_connection = MagicMock()
        mock_connection.provider = "google"

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_connection
            mock_execute.return_value = mock_result

            await oauth_service.unlink_oauth_account(db=db_session, user=sample_user, provider="google")

            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_unlink_oauth_account_not_found(self, oauth_service, db_session, sample_user):
        """Test unlinking OAuth account when connection not found."""
        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_execute.return_value = mock_result

            with pytest.raises(ValueError, match="OAuth connection for google not found"):
                await oauth_service.unlink_oauth_account(
                    db=db_session, user=sample_user, provider="google"
                )

    @pytest.mark.asyncio
    async def test_get_user_oauth_connections_success(self, oauth_service, db_session, sample_user):
        """Test getting user OAuth connections."""
        mock_connection = MagicMock()
        mock_connection.provider = "google"

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_connection]
            mock_execute.return_value = mock_result

            connections = await oauth_service.get_user_oauth_connections(db=db_session, user=sample_user)

            assert len(connections) == 1
            assert connections[0].provider == "google"
