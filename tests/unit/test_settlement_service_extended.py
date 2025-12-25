"""Extended tests for SettlementService methods."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.settlement_service import SettlementService


class TestSettlementServiceExtended:
    """Extended tests for SettlementService class."""

    @pytest.fixture
    def mock_settlement_provider(self):
        """Create mock settlement provider."""
        provider = MagicMock()
        provider.execute_trade = AsyncMock(return_value={"tx_hash": "0xhash", "status": "success"})
        provider.get_transaction_status = AsyncMock(return_value={"status": "confirmed"})
        return provider

    @pytest.fixture
    def settlement_service(self, mock_settlement_provider):
        """Create SettlementService with provider."""
        return SettlementService(settlement_provider=mock_settlement_provider)

    @pytest.mark.asyncio
    async def test_execute_trade_success(self, settlement_service, mock_settlement_provider):
        """Test successful trade execution."""
        result = await settlement_service.execute_trade(
            collateral=1000.0,
            leverage=10,
            asset_type=1,
            direction=True,
            order_type="MARKET",
        )

        assert result["tx_hash"] == "0xhash"
        mock_settlement_provider.execute_trade.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_trade_invalid_collateral(self, settlement_service):
        """Test trade execution with invalid collateral."""
        with pytest.raises(ValueError, match="Collateral must be greater than 0"):
            await settlement_service.execute_trade(
                collateral=0,
                leverage=10,
                asset_type=1,
                direction=True,
                order_type="MARKET",
            )

    @pytest.mark.asyncio
    async def test_execute_trade_invalid_leverage(self, settlement_service):
        """Test trade execution with invalid leverage."""
        with pytest.raises(ValueError, match="Leverage must be at least 1"):
            await settlement_service.execute_trade(
                collateral=1000.0,
                leverage=0,
                asset_type=1,
                direction=True,
                order_type="MARKET",
            )

    @pytest.mark.asyncio
    async def test_execute_trade_with_router(self):
        """Test trade execution using router."""
        mock_router = MagicMock()
        mock_provider = MagicMock()
        mock_provider.execute_trade = AsyncMock(return_value={"tx_hash": "0xhash"})
        mock_router.get_settlement_provider = AsyncMock(return_value=mock_provider)

        with patch("app.services.settlement_service.get_provider_router", return_value=mock_router):
            service = SettlementService(settlement_provider=None)
            service.router = mock_router

            result = await service.execute_trade(
                collateral=1000.0,
                leverage=10,
                asset_type=1,
                direction=True,
                order_type="MARKET",
                asset="BTC",
            )

            assert result["tx_hash"] == "0xhash"
            mock_router.get_settlement_provider.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_transaction_status_success(self, settlement_service, mock_settlement_provider):
        """Test getting transaction status successfully."""
        result = await settlement_service.get_transaction_status("0xhash123")

        assert result["status"] == "confirmed"
        mock_settlement_provider.get_transaction_status.assert_called_once_with("0xhash123")

    @pytest.mark.asyncio
    async def test_get_transaction_status_no_provider(self):
        """Test getting transaction status without provider."""
        service = SettlementService(settlement_provider=None)
        service.router = None

        with pytest.raises(ValueError, match="Settlement provider not configured"):
            await service.get_transaction_status("0xhash123")

