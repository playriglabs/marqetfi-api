"""Test repository classes."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.wallet import Wallet
from app.repositories.base import BaseRepository
from app.repositories.user_repository import UserRepository
from app.repositories.wallet_repository import WalletRepository


class TestBaseRepository:
    """Test BaseRepository class."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock(spec=AsyncSession)
        db.execute = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.delete = AsyncMock()
        return db

    @pytest.fixture
    def user_repo(self):
        """Create UserRepository instance."""
        return UserRepository()

    @pytest.mark.asyncio
    async def test_get_success(self, user_repo, mock_db):
        """Test getting record by ID."""
        mock_user = User(id=1, email="test@example.com", username="testuser")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await user_repo.get(mock_db, 1)

        assert result is not None
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_get_not_found(self, user_repo, mock_db):
        """Test getting record when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await user_repo.get(mock_db, 999)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_all(self, user_repo, mock_db):
        """Test getting all records."""
        mock_users = [User(id=i, email=f"test{i}@example.com", username=f"user{i}") for i in range(3)]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_users
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await user_repo.get_all(mock_db, skip=0, limit=10)

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_create(self, user_repo, mock_db):
        """Test creating record."""
        mock_db.refresh = AsyncMock(side_effect=lambda x: setattr(x, "id", 1))

        result = await user_repo.create(
            mock_db, {"email": "test@example.com", "username": "testuser"}
        )

        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update(self, user_repo, mock_db):
        """Test updating record."""
        mock_user = User(id=1, email="test@example.com", username="testuser")
        mock_db.refresh = AsyncMock()

        result = await user_repo.update(mock_db, mock_user, {"username": "updated"})

        assert result.username == "updated"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_success(self, user_repo, mock_db):
        """Test deleting record."""
        mock_user = User(id=1, email="test@example.com", username="testuser")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await user_repo.delete(mock_db, 1)

        assert result is True
        mock_db.delete.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self, user_repo, mock_db):
        """Test deleting record when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await user_repo.delete(mock_db, 999)

        assert result is False


class TestUserRepository:
    """Test UserRepository class."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock(spec=AsyncSession)
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def user_repo(self):
        """Create UserRepository instance."""
        return UserRepository()

    @pytest.mark.asyncio
    async def test_get_by_email_found(self, user_repo, mock_db):
        """Test getting user by email when found."""
        mock_user = User(id=1, email="test@example.com", username="testuser")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await user_repo.get_by_email(mock_db, "test@example.com")

        assert result is not None
        assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_by_email_not_found(self, user_repo, mock_db):
        """Test getting user by email when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await user_repo.get_by_email(mock_db, "nonexistent@example.com")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_username_found(self, user_repo, mock_db):
        """Test getting user by username when found."""
        mock_user = User(id=1, email="test@example.com", username="testuser")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_user)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await user_repo.get_by_username(mock_db, "testuser")

        assert result is not None
        assert result.username == "testuser"

    @pytest.mark.asyncio
    async def test_get_by_username_not_found(self, user_repo, mock_db):
        """Test getting user by username when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await user_repo.get_by_username(mock_db, "nonexistent")

        assert result is None


class TestWalletRepository:
    """Test WalletRepository class."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock(spec=AsyncSession)
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def wallet_repo(self):
        """Create WalletRepository instance."""
        return WalletRepository()

    @pytest.mark.asyncio
    async def test_get_by_wallet_address_found(self, wallet_repo, mock_db):
        """Test getting wallet by address when found."""
        mock_wallet = Wallet(
            id=1,
            user_id=1,
            wallet_address="0x1234567890123456789012345678901234567890",
            provider_type="privy",
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_wallet)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await wallet_repo.get_by_wallet_address(
            mock_db, "0x1234567890123456789012345678901234567890"
        )

        assert result is not None
        assert result.wallet_address == "0x1234567890123456789012345678901234567890"

    @pytest.mark.asyncio
    async def test_get_primary_by_user_found(self, wallet_repo, mock_db):
        """Test getting primary wallet for user."""
        mock_wallet = Wallet(
            id=1, user_id=1, wallet_address="0x123", provider_type="privy", is_primary=True
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_wallet)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await wallet_repo.get_primary_by_user(mock_db, 1)

        assert result is not None
        assert result.is_primary is True

    @pytest.mark.asyncio
    async def test_get_by_user(self, wallet_repo, mock_db):
        """Test getting all wallets for user."""
        mock_wallets = [
            Wallet(id=i, user_id=1, wallet_address=f"0x{i}", provider_type="privy")
            for i in range(3)
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_wallets
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await wallet_repo.get_by_user(mock_db, 1)

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_get_by_provider_wallet_id_found(self, wallet_repo, mock_db):
        """Test getting wallet by provider wallet ID."""
        mock_wallet = Wallet(
            id=1,
            user_id=1,
            provider_type="privy",
            provider_wallet_id="privy_wallet_123",
            wallet_address="0x123",
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_wallet)
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await wallet_repo.get_by_provider_wallet_id(mock_db, "privy", "privy_wallet_123")

        assert result is not None
        assert result.provider_wallet_id == "privy_wallet_123"

