"""Test WalletService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.provider import OstiumWallet
from app.services.wallet_providers.exceptions import (
    WalletCreationError,
    WalletNotFoundError,
    WalletSigningError,
)
from app.services.wallet_service import WalletService


class TestWalletService:
    """Test WalletService class."""

    @pytest.fixture
    def db_session(self):
        """Create mock database session."""
        return MagicMock(spec=AsyncSession)

    @pytest.fixture
    def service(self, db_session):
        """Create WalletService instance."""
        return WalletService(db_session)

    @pytest.fixture
    def mock_wallet_provider(self):
        """Create mock wallet provider."""
        mock_provider = MagicMock()
        mock_provider.create_wallet = AsyncMock(
            return_value={
                "wallet_id": "test_wallet_id",
                "address": "0x1234567890123456789012345678901234567890",
                "network": "testnet",
                "metadata": {"key": "value"},
            }
        )
        mock_provider.sign_transaction = AsyncMock(return_value="0x" + "a" * 64)
        mock_provider.sign_message = AsyncMock(return_value="0x" + "b" * 64)
        return mock_provider

    @pytest.fixture
    def sample_wallet(self):
        """Create sample wallet model."""
        from datetime import datetime

        wallet = OstiumWallet(
            id=1,
            provider_type="privy",
            provider_wallet_id="test_wallet_id",
            wallet_address="0x1234567890123456789012345678901234567890",
            network="testnet",
            is_active=True,
            metadata={"test": "data"},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        return wallet

    @pytest.mark.asyncio
    async def test_create_wallet_success(self, service, mock_wallet_provider, sample_wallet):
        """Test successful wallet creation."""
        with patch("app.services.wallet_service.WalletProviderFactory.get_provider") as mock_get:
            mock_get.return_value = mock_wallet_provider

            # Mock repository methods
            service.repository.get_by_provider_wallet_id = AsyncMock(return_value=None)
            service.repository.create = AsyncMock(return_value=sample_wallet)

            result = await service.create_wallet("privy", "testnet", {"extra": "metadata"})

            assert result["id"] == 1
            assert result["provider_type"] == "privy"
            assert result["wallet_address"] == "0x1234567890123456789012345678901234567890"
            assert result["network"] == "testnet"
            assert result["is_active"] is True
            mock_wallet_provider.create_wallet.assert_called_once_with("testnet")
            service.repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_wallet_existing(self, service, mock_wallet_provider, sample_wallet):
        """Test wallet creation when wallet already exists."""
        with patch("app.services.wallet_service.WalletProviderFactory.get_provider") as mock_get:
            mock_get.return_value = mock_wallet_provider

            # Mock repository to return existing wallet
            service.repository.get_by_provider_wallet_id = AsyncMock(return_value=sample_wallet)
            mock_create = AsyncMock()
            service.repository.create = mock_create

            result = await service.create_wallet("privy", "testnet")

            assert result["id"] == 1
            assert result["provider_type"] == "privy"
            # Should not create new wallet
            mock_create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_wallet_invalid_data(self, service, mock_wallet_provider):
        """Test wallet creation with invalid data from provider."""
        with patch("app.services.wallet_service.WalletProviderFactory.get_provider") as mock_get:
            mock_get.return_value = mock_wallet_provider

            # Provider returns invalid data (missing wallet_id or address)
            mock_wallet_provider.create_wallet = AsyncMock(
                return_value={"wallet_id": "test_id"}  # Missing address
            )

            with pytest.raises(WalletCreationError) as exc_info:
                await service.create_wallet("privy", "testnet")

            assert "Invalid wallet data" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_wallet_success(self, service, sample_wallet):
        """Test getting wallet by ID."""
        service.repository.get = AsyncMock(return_value=sample_wallet)

        result = await service.get_wallet(1)

        assert result["id"] == 1
        assert result["provider_type"] == "privy"
        assert result["wallet_address"] == "0x1234567890123456789012345678901234567890"
        service.repository.get.assert_called_once_with(service.db, 1)

    @pytest.mark.asyncio
    async def test_get_wallet_not_found(self, service):
        """Test getting non-existent wallet."""
        service.repository.get = AsyncMock(return_value=None)

        with pytest.raises(WalletNotFoundError) as exc_info:
            await service.get_wallet(999)

        assert "Wallet not found: 999" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_wallet_by_provider_id_success(self, service, sample_wallet):
        """Test getting wallet by provider ID."""
        service.repository.get_by_provider_wallet_id = AsyncMock(return_value=sample_wallet)

        result = await service.get_wallet_by_provider_id("test_wallet_id")

        assert result["id"] == 1
        assert result["provider_wallet_id"] == "test_wallet_id"
        service.repository.get_by_provider_wallet_id.assert_called_once_with(
            service.db, "test_wallet_id"
        )

    @pytest.mark.asyncio
    async def test_get_wallet_by_provider_id_not_found(self, service):
        """Test getting wallet by non-existent provider ID."""
        service.repository.get_by_provider_wallet_id = AsyncMock(return_value=None)

        with pytest.raises(WalletNotFoundError) as exc_info:
            await service.get_wallet_by_provider_id("nonexistent")

        assert "Wallet not found: nonexistent" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_sign_transaction_success(self, service, mock_wallet_provider, sample_wallet):
        """Test successful transaction signing."""
        with patch("app.services.wallet_service.WalletProviderFactory.get_provider") as mock_get:
            mock_get.return_value = mock_wallet_provider

            service.repository.get = AsyncMock(return_value=sample_wallet)

            transaction = {"to": "0xrecipient", "value": "1000000000000000000"}
            result = await service.sign_transaction(1, transaction)

            assert result == "0x" + "a" * 64
            mock_wallet_provider.sign_transaction.assert_called_once_with(
                "test_wallet_id", transaction
            )

    @pytest.mark.asyncio
    async def test_sign_transaction_wallet_not_found(self, service):
        """Test signing transaction with non-existent wallet."""
        service.repository.get = AsyncMock(return_value=None)

        with pytest.raises(WalletNotFoundError):
            await service.sign_transaction(999, {"to": "0xrecipient"})

    @pytest.mark.asyncio
    async def test_sign_transaction_wallet_inactive(self, service, sample_wallet):
        """Test signing transaction with inactive wallet."""
        sample_wallet.is_active = False
        service.repository.get = AsyncMock(return_value=sample_wallet)

        with pytest.raises(WalletSigningError) as exc_info:
            await service.sign_transaction(1, {"to": "0xrecipient"})

        assert "Wallet is not active" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_sign_transaction_provider_error(
        self, service, mock_wallet_provider, sample_wallet
    ):
        """Test transaction signing when provider fails."""
        with patch("app.services.wallet_service.WalletProviderFactory.get_provider") as mock_get:
            mock_get.return_value = mock_wallet_provider

            service.repository.get = AsyncMock(return_value=sample_wallet)
            mock_wallet_provider.sign_transaction = AsyncMock(
                side_effect=Exception("Provider error")
            )

            with pytest.raises(WalletSigningError) as exc_info:
                await service.sign_transaction(1, {"to": "0xrecipient"})

            assert "Failed to sign transaction" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_sign_message_success(self, service, mock_wallet_provider, sample_wallet):
        """Test successful message signing."""
        with patch("app.services.wallet_service.WalletProviderFactory.get_provider") as mock_get:
            mock_get.return_value = mock_wallet_provider

            service.repository.get = AsyncMock(return_value=sample_wallet)

            result = await service.sign_message(1, "Hello, World!")

            assert result == "0x" + "b" * 64
            mock_wallet_provider.sign_message.assert_called_once_with(
                "test_wallet_id", "Hello, World!"
            )

    @pytest.mark.asyncio
    async def test_sign_message_wallet_not_found(self, service):
        """Test signing message with non-existent wallet."""
        service.repository.get = AsyncMock(return_value=None)

        with pytest.raises(WalletNotFoundError):
            await service.sign_message(999, "Hello")

    @pytest.mark.asyncio
    async def test_sign_message_wallet_inactive(self, service, sample_wallet):
        """Test signing message with inactive wallet."""
        sample_wallet.is_active = False
        service.repository.get = AsyncMock(return_value=sample_wallet)

        with pytest.raises(WalletSigningError):
            await service.sign_message(1, "Hello")

    @pytest.mark.asyncio
    async def test_get_active_wallet_success(self, service, sample_wallet):
        """Test getting active wallet."""
        service.repository.get_active_by_provider = AsyncMock(return_value=[sample_wallet])

        result = await service.get_active_wallet("privy", "testnet")

        assert result is not None
        assert result["id"] == 1
        assert result["provider_type"] == "privy"
        service.repository.get_active_by_provider.assert_called_once_with(
            service.db, "privy", "testnet"
        )

    @pytest.mark.asyncio
    async def test_get_active_wallet_none(self, service):
        """Test getting active wallet when none exists."""
        service.repository.get_active_by_provider = AsyncMock(return_value=[])

        result = await service.get_active_wallet("privy", "testnet")

        assert result is None

    @pytest.mark.asyncio
    async def test_list_wallets_with_filters(self, service, sample_wallet):
        """Test listing wallets with provider and network filters."""
        service.repository.get_by_provider_and_network = AsyncMock(return_value=[sample_wallet])

        result = await service.list_wallets(provider_name="privy", network="testnet")

        assert len(result) == 1
        assert result[0]["id"] == 1
        service.repository.get_by_provider_and_network.assert_called_once_with(
            service.db, "privy", "testnet"
        )

    @pytest.mark.asyncio
    async def test_list_wallets_no_filters(self, service, sample_wallet):
        """Test listing all wallets without filters."""
        service.repository.get_all = AsyncMock(return_value=[sample_wallet])

        result = await service.list_wallets()

        assert len(result) == 1
        assert result[0]["id"] == 1
        service.repository.get_all.assert_called_once_with(service.db)

    @pytest.mark.asyncio
    async def test_deactivate_wallet_success(self, service, sample_wallet):
        """Test deactivating wallet."""
        sample_wallet.is_active = False
        service.repository.deactivate = AsyncMock(return_value=sample_wallet)

        result = await service.deactivate_wallet(1)

        assert result["is_active"] is False
        service.repository.deactivate.assert_called_once_with(service.db, 1)

    @pytest.mark.asyncio
    async def test_deactivate_wallet_not_found(self, service):
        """Test deactivating non-existent wallet."""
        service.repository.deactivate = AsyncMock(return_value=None)

        with pytest.raises(WalletNotFoundError):
            await service.deactivate_wallet(999)

    @pytest.mark.asyncio
    async def test_activate_wallet_success(self, service, sample_wallet):
        """Test activating wallet."""
        sample_wallet.is_active = True
        service.repository.activate = AsyncMock(return_value=sample_wallet)

        result = await service.activate_wallet(1)

        assert result["is_active"] is True
        service.repository.activate.assert_called_once_with(service.db, 1)

    @pytest.mark.asyncio
    async def test_activate_wallet_not_found(self, service):
        """Test activating non-existent wallet."""
        service.repository.activate = AsyncMock(return_value=None)

        with pytest.raises(WalletNotFoundError):
            await service.activate_wallet(999)
