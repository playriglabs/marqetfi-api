"""Test SettlementService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.providers.base import BaseSettlementProvider
from app.services.settlement_service import SettlementService


class TestSettlementService:
    """Test SettlementService class."""

    @pytest.fixture
    def mock_settlement_provider(self):
        """Create mock settlement provider."""
        mock_provider = MagicMock(spec=BaseSettlementProvider)
        mock_provider.execute_trade = AsyncMock(
            return_value={"transaction_hash": "0x123", "status": "pending"}
        )
        mock_provider.get_transaction_status = AsyncMock(
            return_value={"status": "confirmed", "block_number": 12345}
        )
        return mock_provider

    @pytest.fixture
    def service_with_provider(self, mock_settlement_provider):
        """Create service with provider."""
        return SettlementService(settlement_provider=mock_settlement_provider)

    @pytest.fixture
    def service_with_router(self):
        """Create service with router."""
        return SettlementService()

    @pytest.mark.asyncio
    async def test_execute_trade_success(self, service_with_provider, mock_settlement_provider):
        """Test successful trade execution."""
        result = await service_with_provider.execute_trade(
            collateral=1000.0,
            leverage=10,
            asset_type=1,
            direction=True,
            order_type="MARKET",
        )

        assert result["transaction_hash"] == "0x123"
        assert result["status"] == "pending"
        mock_settlement_provider.execute_trade.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_trade_invalid_collateral(self, service_with_provider):
        """Test trade execution with invalid collateral."""
        with pytest.raises(ValueError, match="Collateral must be greater than 0"):
            await service_with_provider.execute_trade(
                collateral=0,
                leverage=10,
                asset_type=1,
                direction=True,
                order_type="MARKET",
            )

    @pytest.mark.asyncio
    async def test_execute_trade_invalid_leverage(self, service_with_provider):
        """Test trade execution with invalid leverage."""
        with pytest.raises(ValueError, match="Leverage must be at least 1"):
            await service_with_provider.execute_trade(
                collateral=1000.0,
                leverage=0,
                asset_type=1,
                direction=True,
                order_type="MARKET",
            )

    @pytest.mark.asyncio
    async def test_execute_trade_with_router(self, service_with_router):
        """Test trade execution using router."""
        with patch("app.services.settlement_service.get_provider_router") as mock_router:
            mock_router_instance = MagicMock()
            mock_provider = MagicMock(spec=BaseSettlementProvider)
            mock_provider.execute_trade = AsyncMock(
                return_value={"transaction_hash": "0x456", "status": "pending"}
            )
            mock_router_instance.get_settlement_provider = AsyncMock(return_value=mock_provider)
            mock_router.return_value = mock_router_instance

            service = SettlementService()
            service.router = mock_router_instance

            result = await service.execute_trade(
                collateral=1000.0,
                leverage=10,
                asset_type=1,
                direction=True,
                order_type="MARKET",
                asset="BTC",
            )

            assert result["transaction_hash"] == "0x456"
            mock_router_instance.get_settlement_provider.assert_called_once_with(
                asset="BTC", asset_type=1
            )

    @pytest.mark.asyncio
    async def test_execute_trade_no_provider(self):
        """Test trade execution without provider."""
        # Create service with no provider and no router
        service = SettlementService(settlement_provider=None)
        service.router = None
        with pytest.raises(ValueError, match="Settlement provider not configured"):
            await service.execute_trade(
                collateral=1000.0,
                leverage=10,
                asset_type=1,
                direction=True,
                order_type="MARKET",
            )

    @pytest.mark.asyncio
    async def test_get_transaction_status_success(
        self, service_with_provider, mock_settlement_provider
    ):
        """Test getting transaction status."""
        result = await service_with_provider.get_transaction_status("0x123")

        assert result["status"] == "confirmed"
        assert result["block_number"] == 12345
        mock_settlement_provider.get_transaction_status.assert_called_once_with("0x123")

    @pytest.mark.asyncio
    async def test_get_transaction_status_no_provider(self):
        """Test getting transaction status without provider."""
        service = SettlementService()
        with pytest.raises(ValueError, match="Settlement provider not configured"):
            await service.get_transaction_status("0x123")

