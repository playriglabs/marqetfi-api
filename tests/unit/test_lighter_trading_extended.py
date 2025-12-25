"""Extended tests for LighterTradingProvider."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config.providers.lighter import LighterConfig
from app.services.providers.lighter.trading import LighterTradingProvider


class TestLighterTradingProviderExtended:
    """Extended tests for LighterTradingProvider."""

    @pytest.fixture
    def lighter_config(self):
        """Create Lighter config."""
        return LighterConfig(
            enabled=True,
            api_url="https://api.lighter.xyz",
            api_key="test_key",
            private_key="0x123",
            network="mainnet",
            timeout=30,
            retry_attempts=3,
            retry_delay=1.0,
        )

    @pytest.fixture
    def trading_provider(self, lighter_config):
        """Create LighterTradingProvider instance."""
        return LighterTradingProvider(lighter_config)

    @pytest.mark.asyncio
    async def test_update_tp_success(self, trading_provider):
        """Test updating take profit successfully."""
        with patch.object(trading_provider.lighter_service, "initialize", new_callable=AsyncMock):
            result = await trading_provider.update_tp(pair_id=1, trade_index=0, tp_price=50000.0)

            assert result["status"] == "not_supported"

    @pytest.mark.asyncio
    async def test_update_sl_success(self, trading_provider):
        """Test updating stop loss successfully."""
        with patch.object(trading_provider.lighter_service, "initialize", new_callable=AsyncMock):
            result = await trading_provider.update_sl(pair_id=1, trade_index=0, sl_price=40000.0)

            assert result["status"] == "not_supported"

    @pytest.mark.asyncio
    async def test_get_open_trades_success(self, trading_provider):
        """Test getting open trades successfully."""
        mock_account = {"address": "0x123", "positions": []}

        with (
            patch.object(trading_provider.lighter_service, "initialize", new_callable=AsyncMock),
            patch("app.services.providers.lighter.trading.lighter") as mock_lighter,
            patch("asyncio.to_thread", new_callable=AsyncMock, return_value=mock_account),
        ):
            mock_account_api = MagicMock()
            mock_lighter.AccountApi = MagicMock(return_value=mock_account_api)

            result = await trading_provider.get_open_trades("0x123")

            assert len(result) == 1
            assert result[0]["status"] == "open"

    @pytest.mark.asyncio
    async def test_get_open_trade_metrics_success(self, trading_provider):
        """Test getting open trade metrics."""
        with patch.object(trading_provider.lighter_service, "initialize", new_callable=AsyncMock):
            result = await trading_provider.get_open_trade_metrics(pair_id=1, trade_index=0)

            assert result["status"] == "not_implemented"

    @pytest.mark.asyncio
    async def test_get_orders_success(self, trading_provider):
        """Test getting orders successfully."""
        mock_orders = [{"order_id": "123", "status": "pending"}]

        with (
            patch.object(trading_provider.lighter_service, "initialize", new_callable=AsyncMock),
            patch("app.services.providers.lighter.trading.lighter") as mock_lighter,
            patch("asyncio.to_thread", new_callable=AsyncMock, return_value=mock_orders),
        ):
            mock_order_api = MagicMock()
            mock_lighter.OrderApi = MagicMock(return_value=mock_order_api)

            result = await trading_provider.get_orders("0x123")

            assert len(result) == 1
            assert result[0]["order_id"] == "123"

    @pytest.mark.asyncio
    async def test_cancel_limit_order_success(self, trading_provider):
        """Test cancelling limit order successfully."""
        mock_result = {"id": "order_123", "status": "cancelled"}

        with (
            patch.object(trading_provider.lighter_service, "initialize", new_callable=AsyncMock),
            patch("app.services.providers.lighter.trading.lighter") as mock_lighter,
            patch("asyncio.to_thread", new_callable=AsyncMock, return_value=mock_result),
        ):
            mock_order_api = MagicMock()
            mock_lighter.OrderApi = MagicMock(return_value=mock_order_api)

            result = await trading_provider.cancel_limit_order(pair_id=1, order_index=0)

            assert result["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_update_limit_order_success(self, trading_provider):
        """Test updating limit order successfully."""
        mock_result = {"id": "order_123", "status": "updated"}

        with (
            patch.object(trading_provider.lighter_service, "initialize", new_callable=AsyncMock),
            patch("app.services.providers.lighter.trading.lighter") as mock_lighter,
            patch("asyncio.to_thread", new_callable=AsyncMock, return_value=mock_result),
        ):
            mock_order_api = MagicMock()
            mock_lighter.OrderApi = MagicMock(return_value=mock_order_api)

            result = await trading_provider.update_limit_order(
                pair_id=1, order_index=0, at_price=45000.0
            )

            assert result["status"] == "updated"

    @pytest.mark.asyncio
    async def test_get_open_trades_sdk_not_installed(self, trading_provider):
        """Test getting open trades when SDK not installed."""
        with patch("app.services.providers.lighter.trading.lighter", None):
            with pytest.raises(Exception, match="lighter-python is not installed"):
                await trading_provider.get_open_trades("0x123")

    @pytest.mark.asyncio
    async def test_get_orders_sdk_not_installed(self, trading_provider):
        """Test getting orders when SDK not installed."""
        with patch("app.services.providers.lighter.trading.lighter", None):
            with pytest.raises(Exception, match="lighter-python is not installed"):
                await trading_provider.get_orders("0x123")
