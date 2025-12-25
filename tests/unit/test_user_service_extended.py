"""Extended tests for UserService methods."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.enums import AuthMethod, FeatureAccessLevel, WalletType
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.user_service import UserService


class TestUserServiceExtended:
    """Extended tests for UserService class."""

    @pytest.fixture
    def sample_user(self):
        """Create sample user."""
        return User(
            id=1,
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            is_active=True,
        )

    @pytest.mark.asyncio
    async def test_create_user_success(self, db_session):
        """Test successful user creation."""
        user_data = UserCreate(
            email="new@example.com",
            username="newuser",
            password="password123",
        )

        with patch.object(db_session, "add"), patch.object(
            db_session, "commit", new_callable=AsyncMock
        ), patch.object(db_session, "refresh", new_callable=AsyncMock):
            with patch("app.services.user_service.User") as mock_user_class:
                mock_user = MagicMock()
                mock_user.id = 1
                mock_user.email = "new@example.com"
                mock_user_class.return_value = mock_user

                user = await UserService.create_user(db_session, user_data)

                assert user is not None

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, db_session, sample_user):
        """Test getting user by ID."""
        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = sample_user
            mock_execute.return_value = mock_result

            user = await UserService.get_user_by_id(db_session, user_id=1)

            assert user is not None
            assert user.id == 1

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, db_session):
        """Test getting user by ID when not found."""
        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_execute.return_value = mock_result

            user = await UserService.get_user_by_id(db_session, user_id=999)

            assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, db_session, sample_user):
        """Test getting user by email."""
        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = sample_user
            mock_execute.return_value = mock_result

            user = await UserService.get_user_by_email(db_session, email="test@example.com")

            assert user is not None
            assert user.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, db_session, sample_user):
        """Test successful user authentication."""
        with patch.object(UserService, "get_user_by_email", return_value=sample_user), patch(
            "app.services.user_service.verify_password", return_value=True
        ):
            user = await UserService.authenticate_user(
                db_session, email="test@example.com", password="password123"
            )

            assert user is not None

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, db_session, sample_user):
        """Test authentication with wrong password."""
        with patch.object(UserService, "get_user_by_email", return_value=sample_user), patch(
            "app.services.user_service.verify_password", return_value=False
        ):
            user = await UserService.authenticate_user(
                db_session, email="test@example.com", password="wrong_password"
            )

            assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_no_password(self, db_session, sample_user):
        """Test authentication for user without password."""
        sample_user.hashed_password = None

        with patch.object(UserService, "get_user_by_email", return_value=sample_user):
            user = await UserService.authenticate_user(
                db_session, email="test@example.com", password="password123"
            )

            assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_auth0_id_success(self, db_session, sample_user):
        """Test getting user by Auth0 ID."""
        sample_user.auth0_user_id = "auth0|123"

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = sample_user
            mock_execute.return_value = mock_result

            user = await UserService.get_user_by_auth0_id(db_session, auth0_user_id="auth0|123")

            assert user is not None
            assert user.auth0_user_id == "auth0|123"

    @pytest.mark.asyncio
    async def test_sync_user_from_auth0_new_user(self, db_session):
        """Test syncing new user from Auth0."""
        auth0_userinfo = {
            "sub": "auth0|123",
            "email": "new@example.com",
            "name": "New User",
            "nickname": "newuser",
            "email_verified": True,
        }

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute, patch.object(
            UserService, "get_user_by_email", return_value=None
        ), patch.object(db_session, "add"), patch.object(db_session, "commit", new_callable=AsyncMock), patch.object(
            db_session, "refresh", new_callable=AsyncMock
        ):
            # Mock no existing user
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_execute.return_value = mock_result

            with patch("app.services.user_service.User") as mock_user_class:
                mock_user = MagicMock()
                mock_user.id = 1
                mock_user.email = "new@example.com"
                mock_user_class.return_value = mock_user

                user = await UserService.sync_user_from_auth0(db_session, auth0_userinfo)

                assert user is not None

    @pytest.mark.asyncio
    async def test_sync_user_from_auth0_existing_user(self, db_session, sample_user):
        """Test syncing existing user from Auth0."""
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

            user = await UserService.sync_user_from_auth0(db_session, auth0_userinfo)

            assert user.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_sync_user_from_auth0_google(self, db_session):
        """Test syncing user from Google OAuth."""
        auth0_userinfo = {
            "sub": "google-oauth2|123",
            "email": "google@example.com",
            "name": "Google User",
        }

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute, patch.object(
            UserService, "get_user_by_email", return_value=None
        ), patch.object(db_session, "add"), patch.object(db_session, "commit", new_callable=AsyncMock), patch.object(
            db_session, "refresh", new_callable=AsyncMock
        ):
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_execute.return_value = mock_result

            with patch("app.services.user_service.User") as mock_user_class:
                mock_user = MagicMock()
                mock_user.id = 1
                mock_user.auth_method = AuthMethod.GOOGLE
                mock_user_class.return_value = mock_user

                user = await UserService.sync_user_from_auth0(db_session, auth0_userinfo)

                assert user is not None

