"""Extended tests for TradingService methods."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.trading_service import TradingService


class TestTradingServiceExtended:
    """Extended tests for TradingService class."""

    @pytest.fixture
    def mock_trading_provider(self):
        """Create mock trading provider."""
        provider = MagicMock()
        provider.close_trade = AsyncMock(return_value={"status": "closed"})
        provider.update_tp = AsyncMock(return_value={"status": "updated"})
        provider.update_sl = AsyncMock(return_value={"status": "updated"})
        provider.get_open_trades = AsyncMock(return_value=[])
        provider.get_open_trade_metrics = AsyncMock(return_value={})
        provider.get_orders = AsyncMock(return_value=[])
        provider.cancel_limit_order = AsyncMock(return_value={"status": "cancelled"})
        provider.update_limit_order = AsyncMock(return_value={"status": "updated"})
        provider.get_pairs = AsyncMock(return_value=[{"pair_id": 1, "symbol": "BTCUSDT"}])
        return provider

    @pytest.fixture
    def trading_service(self, mock_trading_provider):
        """Create TradingService with provider."""
        return TradingService(trading_provider=mock_trading_provider)

    @pytest.mark.asyncio
    async def test_close_trade_success(self, trading_service, mock_trading_provider):
        """Test closing trade successfully."""
        result = await trading_service.close_trade(pair_id=1, trade_index=0)

        assert result["status"] == "closed"
        mock_trading_provider.close_trade.assert_called_once_with(1, 0)

    @pytest.mark.asyncio
    async def test_close_trade_no_provider(self):
        """Test closing trade without provider."""
        service = TradingService(trading_provider=None)

        with pytest.raises(ValueError, match="Trading provider not configured"):
            await service.close_trade(pair_id=1, trade_index=0)

    @pytest.mark.asyncio
    async def test_update_tp_success(self, trading_service, mock_trading_provider):
        """Test updating take profit successfully."""
        result = await trading_service.update_tp(pair_id=1, trade_index=0, tp_price=50000.0)

        assert result["status"] == "updated"
        mock_trading_provider.update_tp.assert_called_once_with(1, 0, 50000.0)

    @pytest.mark.asyncio
    async def test_update_tp_invalid_price(self, trading_service):
        """Test updating take profit with invalid price."""
        with pytest.raises(ValueError, match="Take profit price must be greater than 0"):
            await trading_service.update_tp(pair_id=1, trade_index=0, tp_price=0)

    @pytest.mark.asyncio
    async def test_update_sl_success(self, trading_service, mock_trading_provider):
        """Test updating stop loss successfully."""
        result = await trading_service.update_sl(pair_id=1, trade_index=0, sl_price=40000.0)

        assert result["status"] == "updated"
        mock_trading_provider.update_sl.assert_called_once_with(1, 0, 40000.0)

    @pytest.mark.asyncio
    async def test_update_sl_invalid_price(self, trading_service):
        """Test updating stop loss with invalid price."""
        with pytest.raises(ValueError, match="Stop loss price must be greater than 0"):
            await trading_service.update_sl(pair_id=1, trade_index=0, sl_price=-1)

    @pytest.mark.asyncio
    async def test_get_open_trades_success(self, trading_service, mock_trading_provider):
        """Test getting open trades successfully."""
        result = await trading_service.get_open_trades(trader_address="0x123")

        assert isinstance(result, list)
        mock_trading_provider.get_open_trades.assert_called_once_with("0x123")

    @pytest.mark.asyncio
    async def test_get_open_trade_metrics_success(self, trading_service, mock_trading_provider):
        """Test getting open trade metrics successfully."""
        result = await trading_service.get_open_trade_metrics(pair_id=1, trade_index=0)

        assert isinstance(result, dict)
        mock_trading_provider.get_open_trade_metrics.assert_called_once_with(1, 0)

    @pytest.mark.asyncio
    async def test_get_orders_success(self, trading_service, mock_trading_provider):
        """Test getting orders successfully."""
        result = await trading_service.get_orders(trader_address="0x123")

        assert isinstance(result, list)
        mock_trading_provider.get_orders.assert_called_once_with("0x123")

    @pytest.mark.asyncio
    async def test_cancel_limit_order_success(self, trading_service, mock_trading_provider):
        """Test cancelling limit order successfully."""
        result = await trading_service.cancel_limit_order(pair_id=1, order_index=0)

        assert result["status"] == "cancelled"
        mock_trading_provider.cancel_limit_order.assert_called_once_with(1, 0)

    @pytest.mark.asyncio
    async def test_update_limit_order_success(self, trading_service, mock_trading_provider):
        """Test updating limit order successfully."""
        result = await trading_service.update_limit_order(pair_id=1, order_index=0, at_price=45000.0)

        assert result["status"] == "updated"
        mock_trading_provider.update_limit_order.assert_called_once_with(1, 0, 45000.0)

    @pytest.mark.asyncio
    async def test_update_limit_order_invalid_price(self, trading_service):
        """Test updating limit order with invalid price."""
        with pytest.raises(ValueError, match="Order price must be greater than 0"):
            await trading_service.update_limit_order(pair_id=1, order_index=0, at_price=0)

    @pytest.mark.asyncio
    async def test_get_pairs_with_provider(self, trading_service, mock_trading_provider):
        """Test getting pairs with provider."""
        result = await trading_service.get_pairs()

        assert len(result) == 1
        mock_trading_provider.get_pairs.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_pairs_with_category(self):
        """Test getting pairs with category filter."""
        mock_router = MagicMock()
        mock_router._category_provider_map = {"crypto": "ostium"}
        mock_provider = MagicMock()
        mock_provider.get_pairs = AsyncMock(return_value=[{"pair_id": 1, "symbol": "BTCUSDT"}])

        with patch("app.services.trading_service.get_provider_router", return_value=mock_router), patch(
            "app.services.trading_service.ProviderFactory.get_trading_provider", return_value=mock_provider
        ):
            service = TradingService(trading_provider=None)
            service.router = mock_router

            result = await service.get_pairs(category="crypto")

            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_pairs_with_router_all_providers(self):
        """Test getting pairs from all providers via router."""
        mock_router = MagicMock()
        mock_router._category_provider_map = {}
        mock_provider = MagicMock()
        mock_provider.get_pairs = AsyncMock(return_value=[{"pair_id": 1, "symbol": "BTCUSDT"}])

        with patch("app.services.trading_service.get_provider_router", return_value=mock_router), patch(
            "app.services.trading_service.ProviderFactory.get_trading_provider", return_value=mock_provider
        ):
            service = TradingService(trading_provider=None)
            service.router = mock_router

            result = await service.get_pairs()

            assert len(result) >= 1

    @pytest.mark.asyncio
    async def test_get_pairs_no_provider(self):
        """Test getting pairs without provider."""
        service = TradingService(trading_provider=None)
        service.router = None

        with pytest.raises(ValueError, match="Trading provider not configured"):
            await service.get_pairs()

