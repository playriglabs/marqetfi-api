"""Test DepositService."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deposit import Deposit, TokenSwap
from app.services.deposit_service import DepositService


class TestDepositService:
    """Test DepositService class."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock(spec=AsyncSession)

    @pytest.fixture
    def service(self, mock_db):
        """Create DepositService instance."""
        return DepositService(db=mock_db)

    @pytest.fixture
    def sample_deposit(self):
        """Create sample deposit."""
        deposit = Deposit(
            id=1,
            user_id=1,
            token_address="0x123",
            token_symbol="USDT",
            chain="arbitrum",
            amount=Decimal("100.0"),
            status="pending",
            provider="ostium",
        )
        return deposit

    @pytest.mark.asyncio
    async def test_process_deposit_no_swap(self, service, mock_db, sample_deposit):
        """Test processing deposit without swap."""
        service.deposit_repo.create = AsyncMock(return_value=sample_deposit)
        service.deposit_repo.update = AsyncMock(return_value=sample_deposit)
        service.check_swap_needed = AsyncMock(return_value=False)

        result = await service.process_deposit(
            user_id=1,
            token_address="0x123",
            token_symbol="USDC",
            chain="arbitrum",
            amount=Decimal("100.0"),
            provider="ostium",
        )

        assert result.status == "completed"
        service.deposit_repo.create.assert_called_once()
        service.deposit_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_deposit_with_swap(self, service, mock_db, sample_deposit):
        """Test processing deposit with swap."""
        service.deposit_repo.create = AsyncMock(return_value=sample_deposit)
        service.deposit_repo.update = AsyncMock(return_value=sample_deposit)
        service.check_swap_needed = AsyncMock(return_value=True)
        service.execute_automatic_swap = AsyncMock(return_value=MagicMock(spec=TokenSwap))

        result = await service.process_deposit(
            user_id=1,
            token_address="0x123",
            token_symbol="USDT",
            chain="ethereum",
            amount=Decimal("100.0"),
            provider="ostium",
        )

        assert result.status == "processing"
        service.execute_automatic_swap.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_deposit_swap_fails(self, service, mock_db, sample_deposit):
        """Test processing deposit when swap fails."""
        service.deposit_repo.create = AsyncMock(return_value=sample_deposit)
        service.deposit_repo.update = AsyncMock(return_value=sample_deposit)
        service.check_swap_needed = AsyncMock(return_value=True)
        service.execute_automatic_swap = AsyncMock(side_effect=Exception("Swap failed"))

        with pytest.raises(Exception, match="Swap failed"):
            await service.process_deposit(
                user_id=1,
                token_address="0x123",
                token_symbol="USDT",
                chain="ethereum",
                amount=Decimal("100.0"),
                provider="ostium",
            )

        # Should mark deposit as failed
        assert service.deposit_repo.update.call_count >= 2

    @pytest.mark.asyncio
    async def test_check_swap_needed_ostium_token_mismatch(self, service):
        """Test checking swap needed for Ostium with token mismatch."""
        with patch("app.services.deposit_service.ProviderFactory") as mock_factory:
            mock_config = MagicMock()
            mock_config.required_token = "USDC"
            mock_config.required_chain = "arbitrum"
            mock_factory._get_provider_config = AsyncMock(return_value=mock_config)

            result = await service.check_swap_needed("USDT", "arbitrum", "ostium")

            assert result is True  # Token mismatch

    @pytest.mark.asyncio
    async def test_check_swap_needed_ostium_chain_mismatch(self, service):
        """Test checking swap needed for Ostium with chain mismatch."""
        with patch("app.services.deposit_service.ProviderFactory") as mock_factory:
            mock_config = MagicMock()
            mock_config.required_token = "USDC"
            mock_config.required_chain = "arbitrum"
            mock_factory._get_provider_config = AsyncMock(return_value=mock_config)

            result = await service.check_swap_needed("USDC", "ethereum", "ostium")

            assert result is True  # Chain mismatch

    @pytest.mark.asyncio
    async def test_check_swap_needed_no_swap(self, service):
        """Test checking swap needed when no swap required."""
        with patch("app.services.deposit_service.ProviderFactory") as mock_factory:
            mock_config = MagicMock()
            mock_config.required_token = "USDC"
            mock_config.required_chain = "arbitrum"
            mock_factory._get_provider_config = AsyncMock(return_value=mock_config)

            result = await service.check_swap_needed("USDC", "arbitrum", "ostium")

            assert result is False

    @pytest.mark.asyncio
    async def test_check_swap_needed_config_fallback(self, service):
        """Test checking swap needed with config fallback."""
        with patch("app.services.deposit_service.ProviderFactory") as mock_factory:
            mock_factory._get_provider_config = AsyncMock(side_effect=Exception("Config error"))

            with patch("app.services.deposit_service.get_settings") as mock_settings:
                mock_settings.return_value = MagicMock(
                    ostium_required_token="USDC", ostium_required_chain="arbitrum"
                )

                result = await service.check_swap_needed("USDC", "arbitrum", "ostium")

                assert result is False

    @pytest.mark.asyncio
    async def test_execute_automatic_swap_success(self, service, mock_db, sample_deposit):
        """Test executing automatic swap successfully."""
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
            mock_swap_provider.get_swap_quote = AsyncMock(
                return_value={"estimated_amount": "99.5"}
            )
            mock_factory.get_swap_provider = AsyncMock(return_value=mock_swap_provider)

            with patch("app.services.deposit_service.ConfigurationService") as mock_config_service:
                mock_config_instance = MagicMock()
                mock_config_instance.get_config_with_fallback = AsyncMock(return_value="lifi")
                mock_config_service.return_value = mock_config_instance

                result = await service.execute_automatic_swap(sample_deposit, "ostium")

                assert result is not None
                service.swap_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_deposit_success(self, service, mock_db, sample_deposit):
        """Test getting deposit by ID."""
        service.deposit_repo.get = AsyncMock(return_value=sample_deposit)

        result = await service.get_deposit(1)

        assert result is not None
        assert result.id == 1
        service.deposit_repo.get.assert_called_once_with(mock_db, 1)

    @pytest.mark.asyncio
    async def test_get_deposit_not_found(self, service, mock_db):
        """Test getting deposit when not found."""
        service.deposit_repo.get = AsyncMock(return_value=None)

        result = await service.get_deposit(999)

        assert result is None

    @pytest.mark.asyncio
    async def test_list_deposits_by_user(self, service, mock_db):
        """Test listing deposits by user."""
        deposits = [MagicMock(spec=Deposit) for _ in range(3)]
        service.deposit_repo.get_by_user = AsyncMock(return_value=deposits)

        result = await service.list_deposits(user_id=1)

        assert len(result) == 3
        service.deposit_repo.get_by_user.assert_called_once_with(mock_db, 1, 0, 100)

    @pytest.mark.asyncio
    async def test_list_deposits_by_status(self, service, mock_db):
        """Test listing deposits by status."""
        deposits = [MagicMock(spec=Deposit) for _ in range(2)]
        service.deposit_repo.get_by_status = AsyncMock(return_value=deposits)

        result = await service.list_deposits(status="completed")

        assert len(result) == 2
        service.deposit_repo.get_by_status.assert_called_once_with(mock_db, "completed", 0, 100)

    @pytest.mark.asyncio
    async def test_list_deposits_by_provider(self, service, mock_db):
        """Test listing deposits by provider."""
        deposits = [MagicMock(spec=Deposit) for _ in range(1)]
        service.deposit_repo.get_by_provider = AsyncMock(return_value=deposits)

        result = await service.list_deposits(provider="ostium")

        assert len(result) == 1
        service.deposit_repo.get_by_provider.assert_called_once_with(mock_db, "ostium", 0, 100)

    @pytest.mark.asyncio
    async def test_list_deposits_all(self, service, mock_db):
        """Test listing all deposits."""
        deposits = [MagicMock(spec=Deposit) for _ in range(5)]
        service.deposit_repo.get_all = AsyncMock(return_value=deposits)

        result = await service.list_deposits()

        assert len(result) == 5
        service.deposit_repo.get_all.assert_called_once_with(mock_db, 0, 100)

    @pytest.mark.asyncio
    async def test_get_swap_status_no_swap(self, service, mock_db, sample_deposit):
        """Test getting swap status when no swap needed."""
        service.get_deposit = AsyncMock(return_value=sample_deposit)
        service.swap_repo.get_by_deposit = AsyncMock(return_value=[])

        result = await service.get_swap_status(1)

        assert result["swap_needed"] is False
        assert len(result["swaps"]) == 0

    @pytest.mark.asyncio
    async def test_get_swap_status_with_swap(self, service, mock_db, sample_deposit):
        """Test getting swap status with swap."""
        mock_swap = MagicMock(spec=TokenSwap)
        mock_swap.id = 1
        mock_swap.swap_status = "pending"
        mock_swap.from_token = "0xUSDT"
        mock_swap.to_token = "0xUSDC"
        mock_swap.from_chain = "ethereum"
        mock_swap.to_chain = "arbitrum"
        mock_swap.amount = Decimal("100.0")
        mock_swap.estimated_output = Decimal("99.5")
        mock_swap.actual_output = None
        mock_swap.swap_transaction_hash = None
        mock_swap.error_message = None

        service.get_deposit = AsyncMock(return_value=sample_deposit)
        service.swap_repo.get_by_deposit = AsyncMock(return_value=[mock_swap])

        result = await service.get_swap_status(1)

        assert result["swap_needed"] is True
        assert len(result["swaps"]) == 1
        assert result["swaps"][0]["status"] == "pending"

