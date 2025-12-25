"""Test authentication service."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.enums import AuthMethod, FeatureAccessLevel, WalletType
from app.models.user import User
from app.services.auth_service import AuthenticationService


class TestAuthenticationService:
    """Test AuthenticationService class."""

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
    async def test_register_with_email_success(self, auth_service, db_session):
        """Test successful email registration."""
        from app.models.user import User
        from app.models.enums import AuthMethod, FeatureAccessLevel, WalletType

        mock_user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            auth0_user_id="auth0_123",
            auth_method=AuthMethod.EMAIL,
            wallet_type=WalletType.NONE,
            feature_access_level=FeatureAccessLevel.FULL,
        )

        with patch.object(
            auth_service.user_service, "get_user_by_email", return_value=None
        ), patch("app.services.auth_service.Auth0Service") as mock_auth0_class, patch.object(
            auth_service, "_generate_tokens", return_value={"access_token": "token", "refresh_token": "refresh"}
        ), patch.object(db_session, "add"), patch.object(db_session, "commit", new_callable=AsyncMock), patch.object(
            db_session, "refresh", new_callable=AsyncMock
        ):
            mock_auth0_service = MagicMock()
            mock_auth0_service.register_user = AsyncMock(
                return_value={"user_id": "auth0_123", "email": "test@example.com"}
            )
            mock_auth0_class.return_value = mock_auth0_service

            # Mock the user creation
            with patch("app.services.auth_service.User", return_value=mock_user):
                user, tokens = await auth_service.register_with_email(
                    db=db_session, email="test@example.com", password="password123", username="testuser"
                )

                assert user.email == "test@example.com"
                assert "access_token" in tokens

    @pytest.mark.asyncio
    async def test_register_with_email_existing_user(self, auth_service, db_session, sample_user):
        """Test registration with existing email."""
        with patch.object(
            auth_service.user_service, "get_user_by_email", return_value=sample_user
        ):
            with pytest.raises(ValueError, match="User with this email already exists"):
                await auth_service.register_with_email(
                    db=db_session, email="test@example.com", password="password123"
                )

    @pytest.mark.asyncio
    async def test_login_with_email_success(self, auth_service, db_session, sample_user):
        """Test successful email login."""
        with patch("app.services.auth_service.Auth0Service") as mock_auth0_class, patch.object(
            auth_service.user_service, "get_user_by_email", return_value=sample_user
        ), patch.object(auth_service, "_generate_tokens", return_value={"access_token": "token", "refresh_token": "refresh"}):
            mock_auth0_service = MagicMock()
            mock_auth0_service.login = AsyncMock(return_value={"access_token": "auth0_token"})
            mock_auth0_class.return_value = mock_auth0_service

            user, tokens = await auth_service.login_with_email(
                db=db_session, email="test@example.com", password="password123"
            )

            assert user.email == "test@example.com"
            assert "access_token" in tokens

    @pytest.mark.asyncio
    async def test_login_with_email_invalid_credentials(self, auth_service, db_session):
        """Test login with invalid credentials."""
        with patch("app.services.auth_service.Auth0Service") as mock_auth0_class:
            mock_auth0_service = MagicMock()
            mock_auth0_service.login = AsyncMock(side_effect=ValueError("Invalid credentials"))
            mock_auth0_class.return_value = mock_auth0_service

            with pytest.raises(ValueError, match="Invalid credentials"):
                await auth_service.login_with_email(
                    db=db_session, email="test@example.com", password="wrong"
                )

    @pytest.mark.asyncio
    async def test_handle_provider_authentication_success(self, auth_service, db_session, sample_user):
        """Test successful provider authentication."""
        with patch("app.services.auth_service.ProviderFactory") as mock_factory, patch.object(
            auth_service.user_service, "get_or_create_user_from_provider", return_value=sample_user
        ), patch.object(auth_service, "_generate_tokens", return_value={"access_token": "token", "refresh_token": "refresh"}):
            mock_provider = MagicMock()
            mock_provider.verify_access_token = AsyncMock(return_value={"sub": "user123"})
            mock_provider.get_user_by_id = AsyncMock(return_value={"email": "test@example.com"})
            mock_factory.get_auth_provider = MagicMock(return_value=mock_provider)

            user, tokens = await auth_service.handle_provider_authentication(
                db=db_session, access_token="provider_token", provider_name="privy"
            )

            assert user.email == "test@example.com"
            assert "access_token" in tokens

    @pytest.mark.asyncio
    async def test_refresh_access_token_success(self, auth_service, db_session, sample_user):
        """Test successful token refresh."""
        from app.models.auth import Session

        mock_session = MagicMock(spec=Session)
        mock_session.user_id = 1
        mock_session.refresh_token = "refresh_token"
        mock_session.expires_at = datetime.utcnow() + timedelta(days=7)

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_session
            mock_execute.return_value = mock_result

            with patch.object(auth_service, "_generate_tokens", return_value={"access_token": "new_token", "refresh_token": "refresh"}):
                tokens = await auth_service.refresh_access_token(db=db_session, refresh_token="refresh_token")

                assert "access_token" in tokens

    @pytest.mark.asyncio
    async def test_refresh_access_token_invalid(self, auth_service, db_session):
        """Test token refresh with invalid refresh token."""
        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_execute.return_value = mock_result

            with pytest.raises(ValueError, match="Invalid refresh token"):
                await auth_service.refresh_access_token(db=db_session, refresh_token="invalid")

