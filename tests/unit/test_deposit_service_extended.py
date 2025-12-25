"""Extended tests for DepositService methods."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.deposit import Deposit, TokenSwap
from app.services.deposit_service import DepositService


class TestDepositServiceExtended:
    """Extended tests for DepositService class."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create DepositService instance."""
        return DepositService(db=mock_db)

    @pytest.fixture
    def sample_deposit(self):
        """Create sample deposit."""
        return Deposit(
            id=1,
            user_id=1,
            token_address="0x123",
            token_symbol="USDT",
            chain="arbitrum",
            amount=Decimal("100.0"),
            status="pending",
            provider="ostium",
        )

    @pytest.mark.asyncio
    async def test_get_deposit_with_user_id(self, service, mock_db, sample_deposit):
        """Test getting deposit with user ID filter."""
        service.deposit_repo.get = AsyncMock(return_value=sample_deposit)

        result = await service.get_deposit(deposit_id=1, user_id=1)

        assert result is not None
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_get_deposit_wrong_user(self, service, mock_db, sample_deposit):
        """Test getting deposit with wrong user ID."""
        service.deposit_repo.get = AsyncMock(return_value=sample_deposit)
        sample_deposit.user_id = 2  # Different user

        result = await service.get_deposit(deposit_id=1, user_id=1)

        assert result is None

    @pytest.mark.asyncio
    async def test_list_deposits_with_pagination(self, service, mock_db):
        """Test listing deposits with pagination."""
        deposits = [MagicMock(spec=Deposit) for _ in range(5)]
        service.deposit_repo.get_by_user = AsyncMock(return_value=deposits)

        result = await service.list_deposits(user_id=1, skip=10, limit=5)

        assert len(result) == 5
        service.deposit_repo.get_by_user.assert_called_once_with(mock_db, 1, 10, 5)

    @pytest.mark.asyncio
    async def test_count_deposits_by_user(self, service, mock_db):
        """Test counting deposits by user."""
        service.deposit_repo.get_by_user = AsyncMock(return_value=[MagicMock() for _ in range(3)])

        count = await service.count_deposits(user_id=1)

        assert count == 3

    @pytest.mark.asyncio
    async def test_get_deposit_swap_status_success(self, service, mock_db, sample_deposit):
        """Test getting deposit swap status successfully."""
        mock_swap = MagicMock(spec=TokenSwap)
        mock_swap.id = 1
        mock_swap.deposit_id = 1
        mock_swap.swap_status = "completed"
        mock_swap.from_token = "USDT"
        mock_swap.to_token = "USDC"
        mock_swap.from_amount = Decimal("100.0")
        mock_swap.to_amount = Decimal("99.5")
        mock_swap.swap_transaction_hash = "0xswap123"
        mock_swap.created_at = None
        mock_swap.updated_at = None

        service.get_deposit = AsyncMock(return_value=sample_deposit)
        service.swap_repo.get_by_deposit = AsyncMock(return_value=[mock_swap])

        result = await service.get_deposit_swap_status(deposit_id=1, user_id=1)

        assert result is not None
        assert result["deposit_id"] == 1
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_get_deposit_swap_status_no_swap(self, service, mock_db, sample_deposit):
        """Test getting deposit swap status when no swap exists."""
        service.get_deposit = AsyncMock(return_value=sample_deposit)
        service.swap_repo.get_by_deposit = AsyncMock(return_value=[])

        result = await service.get_deposit_swap_status(deposit_id=1, user_id=1)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_deposit_swap_status_wrong_user(self, service, mock_db, sample_deposit):
        """Test getting deposit swap status with wrong user ID."""
        sample_deposit.user_id = 2
        service.get_deposit = AsyncMock(return_value=None)

        result = await service.get_deposit_swap_status(deposit_id=1, user_id=1)

        assert result is None

    @pytest.mark.asyncio
    async def test_execute_automatic_swap_lighter(self, service, mock_db, sample_deposit):
        """Test executing automatic swap for Lighter provider."""
        mock_swap = MagicMock(spec=TokenSwap)
        mock_swap.id = 1

        service.swap_repo.create = AsyncMock(return_value=mock_swap)
        service.swap_repo.update = AsyncMock(return_value=mock_swap)

        with patch("app.services.deposit_service.ProviderFactory") as mock_factory:
            mock_config = MagicMock()
            mock_config.required_token = "USDC"
            mock_config.required_chain = "ethereum"
            mock_config.required_token_address = "0xUSDC"
            mock_factory._get_provider_config = AsyncMock(return_value=mock_config)

            mock_swap_provider = MagicMock()
            mock_swap_provider.get_swap_quote = AsyncMock(return_value={"estimated_amount": "99.5"})
            mock_swap_provider.execute_swap = AsyncMock(return_value={"transaction_hash": "0xswap"})
            mock_factory.get_swap_provider = AsyncMock(return_value=mock_swap_provider)

            with patch("app.services.deposit_service.ConfigurationService") as mock_config_service:
                mock_config_instance = MagicMock()
                mock_config_instance.get_config_with_fallback = AsyncMock(return_value="lifi")
                mock_config_service.return_value = mock_config_instance

                result = await service.execute_automatic_swap(sample_deposit, "lighter")

                assert result is not None

    @pytest.mark.asyncio
    async def test_check_swap_needed_lighter(self, service):
        """Test checking swap needed for Lighter provider."""
        with patch("app.services.deposit_service.ProviderFactory") as mock_factory:
            mock_config = MagicMock()
            mock_config.required_token = "USDC"
            mock_config.required_chain = "ethereum"
            mock_factory._get_provider_config = AsyncMock(return_value=mock_config)

            result = await service.check_swap_needed("USDT", "ethereum", "lighter")

            assert result is True  # Token mismatch

    @pytest.mark.asyncio
    async def test_check_swap_needed_unknown_provider(self, service):
        """Test checking swap needed for unknown provider."""
        result = await service.check_swap_needed("USDT", "arbitrum", "unknown")

        assert result is False

    @pytest.mark.asyncio
    async def test_execute_automatic_swap_swap_fails(self, service, mock_db, sample_deposit):
        """Test executing automatic swap when swap execution fails."""
        mock_swap = MagicMock(spec=TokenSwap)
        mock_swap.id = 1

        service.swap_repo.create = AsyncMock(return_value=mock_swap)
        service.swap_repo.update = AsyncMock(return_value=mock_swap)

        with patch("app.services.deposit_service.ProviderFactory") as mock_factory:
            mock_config = MagicMock()
            mock_config.required_token = "USDC"
            mock_config.required_chain = "arbitrum"
            mock_config.required_token_address = "0xUSDC"
            mock_factory._get_provider_config = AsyncMock(return_value=mock_config)

            mock_swap_provider = MagicMock()
            mock_swap_provider.get_swap_quote = AsyncMock(return_value={"estimated_amount": "99.5"})
            mock_swap_provider.execute_swap = AsyncMock(side_effect=Exception("Swap execution failed"))
            mock_factory.get_swap_provider = AsyncMock(return_value=mock_swap_provider)

            with patch("app.services.deposit_service.ConfigurationService") as mock_config_service:
                mock_config_instance = MagicMock()
                mock_config_instance.get_config_with_fallback = AsyncMock(return_value="lifi")
                mock_config_service.return_value = mock_config_instance

                with pytest.raises(Exception, match="Swap execution failed"):
                    await service.execute_automatic_swap(sample_deposit, "ostium")

                # Should update swap with error
                assert service.swap_repo.update.call_count >= 1

