"""Extended tests for AuthenticationService methods."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.enums import AuthMethod, FeatureAccessLevel, WalletType
from app.models.user import User
from app.services.auth_service import AuthenticationService


class TestAuthenticationServiceExtended:
    """Extended tests for AuthenticationService class."""

    @pytest.fixture
    def auth_service(self):
        """Create AuthenticationService instance."""
        return AuthenticationService()

    @pytest.fixture
    def sample_user(self):
        """Create sample user."""
        return User(
            id=1,
            email="test@example.com",
            username="testuser",
            auth_method=AuthMethod.EMAIL,
            wallet_type=WalletType.NONE,
            feature_access_level=FeatureAccessLevel.FULL,
            is_active=True,
        )

    @pytest.mark.asyncio
    async def test_create_or_update_user_from_auth0_new_user(self, auth_service, db_session):
        """Test creating new user from Auth0 userinfo."""
        auth0_userinfo = {
            "sub": "auth0|123",
            "email": "new@example.com",
            "name": "New User",
            "nickname": "newuser",
        }

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute, patch.object(
            auth_service.user_service, "get_user_by_email", return_value=None
        ), patch.object(db_session, "add"), patch.object(db_session, "commit", new_callable=AsyncMock), patch.object(
            db_session, "refresh", new_callable=AsyncMock
        ):
            # Mock no existing user
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_execute.return_value = mock_result

            with patch("app.services.auth_service.User") as mock_user_class:
                mock_user = MagicMock()
                mock_user.id = 1
                mock_user.email = "new@example.com"
                mock_user_class.return_value = mock_user

                user = await auth_service.create_or_update_user_from_auth0(db_session, auth0_userinfo)

                assert user is not None

    @pytest.mark.asyncio
    async def test_create_or_update_user_from_auth0_existing_user(self, auth_service, db_session, sample_user):
        """Test updating existing user from Auth0 userinfo."""
        auth0_userinfo = {
            "sub": "auth0|123",
            "email": "test@example.com",
            "name": "Updated User",
        }

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute, patch.object(
            db_session, "commit", new_callable=AsyncMock
        ), patch.object(db_session, "refresh", new_callable=AsyncMock):
            # Mock existing user
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = sample_user
            mock_execute.return_value = mock_result

            user = await auth_service.create_or_update_user_from_auth0(db_session, auth0_userinfo)

            assert user.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_handle_oauth_callback_success(self, auth_service, db_session, sample_user):
        """Test successful OAuth callback handling."""
        with patch("app.services.auth_service.ProviderFactory") as mock_factory, patch.object(
            auth_service, "create_or_update_user_from_auth0", return_value=sample_user
        ), patch.object(auth_service, "_store_oauth_connection", new_callable=AsyncMock), patch.object(
            auth_service, "_generate_tokens", return_value={"access_token": "token", "refresh_token": "refresh"}
        ):
            mock_provider = MagicMock()
            mock_provider.exchange_code_for_tokens = AsyncMock(
                return_value={"access_token": "token", "refresh_token": "refresh"}
            )
            mock_provider.get_userinfo = AsyncMock(return_value={"sub": "auth0|123", "email": "test@example.com"})
            mock_factory.get_auth_provider = AsyncMock(return_value=mock_provider)

            user, tokens = await auth_service.handle_oauth_callback(
                db=db_session, code="auth_code", redirect_uri="https://app.com/callback"
            )

            assert user.email == "test@example.com"
            assert "access_token" in tokens

    @pytest.mark.asyncio
    async def test_detect_provider_from_token_success(self, auth_service):
        """Test detecting provider from token."""
        with patch("app.services.auth_service.ProviderRegistry") as mock_registry, patch(
            "app.services.auth_service.ProviderFactory"
        ) as mock_factory:
            mock_registry.list_auth_providers.return_value = ["auth0", "privy"]
            mock_provider = MagicMock()
            mock_provider.verify_access_token = AsyncMock(return_value={"sub": "user123"})
            mock_factory.get_auth_provider = AsyncMock(return_value=mock_provider)

            provider = await auth_service._detect_provider_from_token("token")

            assert provider == "auth0"

    @pytest.mark.asyncio
    async def test_detect_provider_from_token_not_found(self, auth_service):
        """Test detecting provider when token doesn't match any provider."""
        with patch("app.services.auth_service.ProviderRegistry") as mock_registry, patch(
            "app.services.auth_service.ProviderFactory"
        ) as mock_factory:
            mock_registry.list_auth_providers.return_value = ["auth0", "privy"]
            mock_provider = MagicMock()
            mock_provider.verify_access_token = AsyncMock(return_value=None)
            mock_factory.get_auth_provider = AsyncMock(return_value=mock_provider)

            provider = await auth_service._detect_provider_from_token("invalid_token")

            assert provider is None

    @pytest.mark.asyncio
    async def test_create_or_update_user_from_provider_auth0(self, auth_service, db_session):
        """Test creating user from Auth0 provider."""
        provider_userinfo = {
            "sub": "auth0|123",
            "email": "test@example.com",
            "email_verified": True,
        }

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute, patch.object(
            auth_service.user_service, "get_user_by_email", return_value=None
        ), patch.object(db_session, "add"), patch.object(db_session, "commit", new_callable=AsyncMock), patch.object(
            db_session, "refresh", new_callable=AsyncMock
        ):
            # Mock no existing user
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_execute.return_value = mock_result

            with patch("app.services.auth_service.User") as mock_user_class:
                mock_user = MagicMock()
                mock_user.id = 1
                mock_user.email = "test@example.com"
                mock_user_class.return_value = mock_user

                user = await auth_service.create_or_update_user_from_provider(
                    db_session, provider_userinfo, "auth0"
                )

                assert user is not None

    @pytest.mark.asyncio
    async def test_create_or_update_user_from_provider_privy(self, auth_service, db_session):
        """Test creating user from Privy provider."""
        provider_userinfo = {
            "id": "privy_123",
            "email": "test@example.com",
            "linked_accounts": [{"type": "email", "address": "test@example.com"}],
        }

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute, patch.object(
            auth_service.user_service, "get_user_by_email", return_value=None
        ), patch.object(db_session, "add"), patch.object(db_session, "commit", new_callable=AsyncMock), patch.object(
            db_session, "refresh", new_callable=AsyncMock
        ):
            # Mock no existing user
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_execute.return_value = mock_result

            with patch("app.services.auth_service.User") as mock_user_class:
                mock_user = MagicMock()
                mock_user.id = 1
                mock_user.email = "test@example.com"
                mock_user_class.return_value = mock_user

                user = await auth_service.create_or_update_user_from_provider(
                    db_session, provider_userinfo, "privy"
                )

                assert user is not None

    @pytest.mark.asyncio
    async def test_create_or_update_user_from_provider_unsupported(self, auth_service, db_session):
        """Test creating user from unsupported provider."""
        provider_userinfo = {"id": "unknown_123"}

        with pytest.raises(ValueError, match="Unsupported authentication provider"):
            await auth_service.create_or_update_user_from_provider(db_session, provider_userinfo, "unknown")

    @pytest.mark.asyncio
    async def test_logout_success(self, auth_service, db_session):
        """Test successful logout."""
        from app.models.auth import Session

        mock_session = MagicMock(spec=Session)
        mock_session.user_id = 1
        mock_session.token_hash = "hash123"
        mock_session.revoked = False

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute, patch.object(
            db_session, "commit", new_callable=AsyncMock
        ):
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_session
            mock_execute.return_value = mock_result

            await auth_service.logout(db_session, user_id=1, token_hash="hash123")

            assert mock_session.revoked is True

    @pytest.mark.asyncio
    async def test_store_oauth_connection_new(self, auth_service, db_session, sample_user):
        """Test storing new OAuth connection."""
        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute, patch.object(
            db_session, "add"
        ), patch.object(db_session, "commit", new_callable=AsyncMock), patch.object(
            db_session, "refresh", new_callable=AsyncMock
        ):
            # Mock no existing connection
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_execute.return_value = mock_result

            with patch("app.services.auth_service.OAuthConnection") as mock_conn_class:
                mock_conn = MagicMock()
                mock_conn.id = 1
                mock_conn_class.return_value = mock_conn

                oauth_conn = await auth_service._store_oauth_connection(
                    db=db_session,
                    user=sample_user,
                    provider="google",
                    provider_user_id="google_123",
                    access_token="token",
                    refresh_token="refresh",
                    expires_in=3600,
                )

                assert oauth_conn is not None

    @pytest.mark.asyncio
    async def test_store_oauth_connection_existing(self, auth_service, db_session, sample_user):
        """Test updating existing OAuth connection."""
        from app.models.auth import OAuthConnection

        mock_conn = MagicMock(spec=OAuthConnection)
        mock_conn.id = 1
        mock_conn.user_id = 1
        mock_conn.provider = "google"

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute, patch.object(
            db_session, "commit", new_callable=AsyncMock
        ), patch.object(db_session, "refresh", new_callable=AsyncMock):
            # Mock existing connection
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_conn
            mock_execute.return_value = mock_result

            oauth_conn = await auth_service._store_oauth_connection(
                db=db_session,
                user=sample_user,
                provider="google",
                provider_user_id="google_123",
                access_token="new_token",
                refresh_token="new_refresh",
                expires_in=3600,
            )

            assert oauth_conn.access_token == "new_token"

