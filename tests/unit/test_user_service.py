"""Test UserService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AuthMethod, FeatureAccessLevel, WalletType
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.user_service import UserService


class TestUserService:
    """Test UserService class."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock(spec=AsyncSession)
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def sample_user(self):
        """Create sample user."""
        user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            auth_method=AuthMethod.EMAIL,
            wallet_type=WalletType.NONE,
            feature_access_level=FeatureAccessLevel.FULL,
        )
        return user

    @pytest.fixture
    def user_create_data(self):
        """Create user creation data."""
        return UserCreate(email="test@example.com", username="testuser", password="password123")

    @pytest.mark.asyncio
    async def test_create_user_success(self, mock_db, user_create_data, sample_user):
        """Test successful user creation."""
        mock_db.refresh = AsyncMock(side_effect=lambda u: setattr(u, "id", 1))

        with patch("app.services.user_service.get_password_hash") as mock_hash:
            mock_hash.return_value = "hashed_password"

            result = await UserService.create_user(mock_db, user_create_data)

            assert result.email == "test@example.com"
            assert result.username == "testuser"
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_hash.assert_called_once_with("password123")

    @pytest.mark.asyncio
    async def test_get_user_by_id_found(self, mock_db, sample_user):
        """Test getting user by ID when found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=sample_user)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await UserService.get_user_by_id(mock_db, 1)

        assert result is not None
        assert result.id == 1
        assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, mock_db):
        """Test getting user by ID when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await UserService.get_user_by_id(mock_db, 999)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_by_email_found(self, mock_db, sample_user):
        """Test getting user by email when found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=sample_user)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await UserService.get_user_by_email(mock_db, "test@example.com")

        assert result is not None
        assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, mock_db):
        """Test getting user by email when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await UserService.get_user_by_email(mock_db, "nonexistent@example.com")

        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, mock_db, sample_user):
        """Test successful user authentication."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=sample_user)
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("app.services.user_service.verify_password") as mock_verify:
            mock_verify.return_value = True

            result = await UserService.authenticate_user(mock_db, "test@example.com", "password123")

            assert result is not None
            assert result.email == "test@example.com"
            mock_verify.assert_called_once_with("password123", "hashed_password")

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, mock_db):
        """Test authentication when user not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await UserService.authenticate_user(mock_db, "nonexistent@example.com", "password")

        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_no_password(self, mock_db, sample_user):
        """Test authentication when user has no password."""
        sample_user.hashed_password = None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=sample_user)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await UserService.authenticate_user(mock_db, "test@example.com", "password")

        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, mock_db, sample_user):
        """Test authentication with wrong password."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=sample_user)
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("app.services.user_service.verify_password") as mock_verify:
            mock_verify.return_value = False

            result = await UserService.authenticate_user(mock_db, "test@example.com", "wrong_password")

            assert result is None
            mock_verify.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_by_auth0_id_found(self, mock_db, sample_user):
        """Test getting user by Auth0 ID when found."""
        sample_user.auth0_user_id = "auth0|123"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=sample_user)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await UserService.get_user_by_auth0_id(mock_db, "auth0|123")

        assert result is not None
        assert result.auth0_user_id == "auth0|123"

    @pytest.mark.asyncio
    async def test_get_user_by_auth0_id_not_found(self, mock_db):
        """Test getting user by Auth0 ID when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await UserService.get_user_by_auth0_id(mock_db, "auth0|999")

        assert result is None

    @pytest.mark.asyncio
    async def test_sync_user_from_auth0_existing_by_id(self, mock_db, sample_user):
        """Test syncing user when user exists by Auth0 ID."""
        sample_user.auth0_user_id = "auth0|123"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=sample_user)
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.refresh = AsyncMock()

        auth0_userinfo = {
            "sub": "auth0|123",
            "email": "updated@example.com",
            "name": "Updated Name",
            "email_verified": True,
        }

        result = await UserService.sync_user_from_auth0(mock_db, auth0_userinfo)

        assert result.email == "updated@example.com"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_user_from_auth0_existing_by_email(self, mock_db, sample_user):
        """Test syncing user when user exists by email."""
        # First call returns None (no Auth0 ID match)
        # Second call returns user by email
        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none = MagicMock(return_value=None)
        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none = MagicMock(return_value=sample_user)
        mock_db.execute = AsyncMock(side_effect=[mock_result1, mock_result2])
        mock_db.refresh = AsyncMock()

        auth0_userinfo = {
            "sub": "auth0|123",
            "email": "test@example.com",
            "name": "Test User",
            "email_verified": True,
        }

        result = await UserService.sync_user_from_auth0(mock_db, auth0_userinfo)

        assert result.auth0_user_id == "auth0|123"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_user_from_auth0_new_user(self, mock_db):
        """Test syncing new user from Auth0."""
        # Both calls return None (user doesn't exist)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.refresh = AsyncMock(side_effect=lambda u: setattr(u, "id", 1))

        auth0_userinfo = {
            "sub": "auth0|123",
            "email": "new@example.com",
            "name": "New User",
            "email_verified": True,
        }

        result = await UserService.sync_user_from_auth0(mock_db, auth0_userinfo)

        assert result.email == "new@example.com"
        assert result.auth0_user_id == "auth0|123"
        assert result.auth_method == AuthMethod.EMAIL
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_user_from_auth0_google(self, mock_db):
        """Test syncing user with Google auth method."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.refresh = AsyncMock(side_effect=lambda u: setattr(u, "id", 1))

        auth0_userinfo = {
            "sub": "google-oauth2|123",
            "email": "google@example.com",
            "name": "Google User",
            "email_verified": True,
        }

        result = await UserService.sync_user_from_auth0(mock_db, auth0_userinfo)

        assert result.auth_method == AuthMethod.GOOGLE

    @pytest.mark.asyncio
    async def test_sync_user_from_auth0_apple(self, mock_db):
        """Test syncing user with Apple auth method."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.refresh = AsyncMock(side_effect=lambda u: setattr(u, "id", 1))

        auth0_userinfo = {
            "sub": "apple|123",
            "email": "apple@example.com",
            "name": "Apple User",
            "email_verified": True,
        }

        result = await UserService.sync_user_from_auth0(mock_db, auth0_userinfo)

        assert result.auth_method == AuthMethod.APPLE

    @pytest.mark.asyncio
    async def test_sync_user_from_auth0_username_from_nickname(self, mock_db):
        """Test syncing user with username from nickname."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.refresh = AsyncMock(side_effect=lambda u: setattr(u, "id", 1))

        auth0_userinfo = {
            "sub": "auth0|123",
            "email": "user@example.com",
            "nickname": "cooluser",
            "email_verified": True,
        }

        result = await UserService.sync_user_from_auth0(mock_db, auth0_userinfo)

        assert result.username == "cooluser"

    @pytest.mark.asyncio
    async def test_sync_user_from_auth0_username_from_email(self, mock_db):
        """Test syncing user with username derived from email."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.refresh = AsyncMock(side_effect=lambda u: setattr(u, "id", 1))

        auth0_userinfo = {
            "sub": "auth0|123",
            "email": "user@example.com",
            "email_verified": True,
        }

        result = await UserService.sync_user_from_auth0(mock_db, auth0_userinfo)

        assert result.username == "user"

