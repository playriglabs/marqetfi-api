"""Test TradingService."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.providers.base import BaseTradingProvider
from app.services.trading_service import TradingService


class TestTradingService:
    """Test TradingService class."""

    @pytest.fixture
    def mock_trading_provider(self):
        """Create mock trading provider."""
        mock_provider = MagicMock(spec=BaseTradingProvider)
        mock_provider.open_trade = AsyncMock(
            return_value={"trade_id": "123", "status": "open"}
        )
        mock_provider.close_trade = AsyncMock(return_value={"status": "closed"})
        mock_provider.update_tp = AsyncMock(return_value={"status": "updated"})
        mock_provider.update_sl = AsyncMock(return_value={"status": "updated"})
        mock_provider.get_open_trades = AsyncMock(return_value=[])
        mock_provider.get_open_trade_metrics = AsyncMock(
            return_value={"pnl": 100.0, "leverage": 10}
        )
        mock_provider.get_orders = AsyncMock(return_value=[])
        mock_provider.cancel_limit_order = AsyncMock(return_value={"status": "cancelled"})
        mock_provider.update_limit_order = AsyncMock(return_value={"status": "updated"})
        mock_provider.get_pairs = AsyncMock(return_value=[{"pair_id": 1, "symbol": "BTC/USD"}])
        return mock_provider

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def service_with_provider(self, mock_trading_provider):
        """Create service with provider."""
        return TradingService(trading_provider=mock_trading_provider)

    @pytest.fixture
    def service_with_router(self, mock_db):
        """Create service with router."""
        # Router is initialized at service creation, so we need to patch it first
        with patch("app.services.trading_service.get_provider_router") as mock_router:
            mock_router_instance = MagicMock()
            mock_router.return_value = mock_router_instance
            service = TradingService(db=mock_db)
            service.router = mock_router_instance
            yield service

    @pytest.mark.asyncio
    async def test_open_trade_success(self, service_with_provider, mock_trading_provider):
        """Test successful trade opening."""
        result = await service_with_provider.open_trade(
            collateral=1000.0,
            leverage=10,
            asset_type=1,
            direction=True,
            order_type="MARKET",
        )

        assert result["trade_id"] == "123"
        mock_trading_provider.open_trade.assert_called_once()

    @pytest.mark.asyncio
    async def test_open_trade_invalid_collateral(self, service_with_provider):
        """Test trade opening with invalid collateral."""
        with pytest.raises(ValueError, match="Collateral must be greater than 0"):
            await service_with_provider.open_trade(
                collateral=0,
                leverage=10,
                asset_type=1,
                direction=True,
                order_type="MARKET",
            )

    @pytest.mark.asyncio
    async def test_open_trade_invalid_leverage(self, service_with_provider):
        """Test trade opening with invalid leverage."""
        with pytest.raises(ValueError, match="Leverage must be at least 1"):
            await service_with_provider.open_trade(
                collateral=1000.0,
                leverage=0,
                asset_type=1,
                direction=True,
                order_type="MARKET",
            )

    @pytest.mark.asyncio
    async def test_open_trade_invalid_order_type(self, service_with_provider):
        """Test trade opening with invalid order type."""
        with pytest.raises(ValueError, match="Order type must be MARKET, LIMIT, or STOP"):
            await service_with_provider.open_trade(
                collateral=1000.0,
                leverage=10,
                asset_type=1,
                direction=True,
                order_type="INVALID",
            )

    @pytest.mark.asyncio
    async def test_open_trade_with_risk_check(self, mock_db):
        """Test trade opening with risk management."""
        with patch("app.services.trading_service.get_provider_router") as mock_router:
            mock_router_instance = MagicMock()
            mock_provider = MagicMock(spec=BaseTradingProvider)
            mock_provider.open_trade = AsyncMock(return_value={"trade_id": "123"})
            mock_router_instance.get_trading_provider = AsyncMock(return_value=mock_provider)
            mock_router.return_value = mock_router_instance

            service = TradingService(db=mock_db)

            with patch("app.services.risk_management_service.RiskManagementService") as mock_risk:
                mock_risk_instance = MagicMock()
                mock_risk_instance.validate_pre_trade = AsyncMock(return_value=(True, None))
                mock_risk.return_value = mock_risk_instance

                result = await service.open_trade(
                    collateral=1000.0,
                    leverage=10,
                    asset_type=1,
                    direction=True,
                    order_type="MARKET",
                    user_id=1,
                    available_balance=Decimal("5000"),
                )

                assert result["trade_id"] == "123"
                mock_risk_instance.validate_pre_trade.assert_called_once()

    @pytest.mark.asyncio
    async def test_open_trade_risk_check_fails(self, mock_db):
        """Test trade opening when risk check fails."""
        with patch("app.services.trading_service.get_provider_router") as mock_router:
            mock_router_instance = MagicMock()
            mock_router.return_value = mock_router_instance

            service = TradingService(db=mock_db)

            with patch("app.services.risk_management_service.RiskManagementService") as mock_risk:
                mock_risk_instance = MagicMock()
                mock_risk_instance.validate_pre_trade = AsyncMock(
                    return_value=(False, "Insufficient balance")
                )
                mock_risk.return_value = mock_risk_instance

                with pytest.raises(ValueError, match="Insufficient balance"):
                    await service.open_trade(
                        collateral=1000.0,
                        leverage=10,
                        asset_type=1,
                        direction=True,
                        order_type="MARKET",
                        user_id=1,
                    )

    @pytest.mark.asyncio
    async def test_open_trade_with_router(self, mock_db):
        """Test trade opening using router."""
        with patch("app.services.trading_service.get_provider_router") as mock_router:
            mock_router_instance = MagicMock()
            mock_provider = MagicMock(spec=BaseTradingProvider)
            mock_provider.open_trade = AsyncMock(return_value={"trade_id": "123"})
            mock_router_instance.get_trading_provider = AsyncMock(return_value=mock_provider)
            mock_router.return_value = mock_router_instance

            service = TradingService(db=mock_db)

            result = await service.open_trade(
                collateral=1000.0,
                leverage=10,
                asset_type=1,
                direction=True,
                order_type="MARKET",
                asset="BTC",
            )

            assert result["trade_id"] == "123"
            mock_router_instance.get_trading_provider.assert_called_once_with(
                asset="BTC", asset_type=1
            )

    @pytest.mark.asyncio
    async def test_close_trade_success(self, service_with_provider, mock_trading_provider):
        """Test successful trade closing."""
        result = await service_with_provider.close_trade(pair_id=1, trade_index=0)

        assert result["status"] == "closed"
        mock_trading_provider.close_trade.assert_called_once_with(1, 0)

    @pytest.mark.asyncio
    async def test_close_trade_no_provider(self):
        """Test closing trade without provider."""
        service = TradingService()
        with pytest.raises(ValueError, match="Trading provider not configured"):
            await service.close_trade(pair_id=1, trade_index=0)

    @pytest.mark.asyncio
    async def test_update_tp_success(self, service_with_provider, mock_trading_provider):
        """Test successful take profit update."""
        result = await service_with_provider.update_tp(pair_id=1, trade_index=0, tp_price=50000.0)

        assert result["status"] == "updated"
        mock_trading_provider.update_tp.assert_called_once_with(1, 0, 50000.0)

    @pytest.mark.asyncio
    async def test_update_tp_invalid_price(self, service_with_provider):
        """Test take profit update with invalid price."""
        with pytest.raises(ValueError, match="Take profit price must be greater than 0"):
            await service_with_provider.update_tp(pair_id=1, trade_index=0, tp_price=0)

    @pytest.mark.asyncio
    async def test_update_sl_success(self, service_with_provider, mock_trading_provider):
        """Test successful stop loss update."""
        result = await service_with_provider.update_sl(pair_id=1, trade_index=0, sl_price=40000.0)

        assert result["status"] == "updated"
        mock_trading_provider.update_sl.assert_called_once_with(1, 0, 40000.0)

    @pytest.mark.asyncio
    async def test_update_sl_invalid_price(self, service_with_provider):
        """Test stop loss update with invalid price."""
        with pytest.raises(ValueError, match="Stop loss price must be greater than 0"):
            await service_with_provider.update_sl(pair_id=1, trade_index=0, sl_price=-100)

    @pytest.mark.asyncio
    async def test_get_open_trades(self, service_with_provider, mock_trading_provider):
        """Test getting open trades."""
        result = await service_with_provider.get_open_trades("0x123")

        assert result == []
        mock_trading_provider.get_open_trades.assert_called_once_with("0x123")

    @pytest.mark.asyncio
    async def test_get_open_trade_metrics(self, service_with_provider, mock_trading_provider):
        """Test getting trade metrics."""
        result = await service_with_provider.get_open_trade_metrics(pair_id=1, trade_index=0)

        assert result["pnl"] == 100.0
        assert result["leverage"] == 10
        mock_trading_provider.get_open_trade_metrics.assert_called_once_with(1, 0)

    @pytest.mark.asyncio
    async def test_get_orders(self, service_with_provider, mock_trading_provider):
        """Test getting orders."""
        result = await service_with_provider.get_orders("0x123")

        assert result == []
        mock_trading_provider.get_orders.assert_called_once_with("0x123")

    @pytest.mark.asyncio
    async def test_cancel_limit_order(self, service_with_provider, mock_trading_provider):
        """Test cancelling limit order."""
        result = await service_with_provider.cancel_limit_order(pair_id=1, order_index=0)

        assert result["status"] == "cancelled"
        mock_trading_provider.cancel_limit_order.assert_called_once_with(1, 0)

    @pytest.mark.asyncio
    async def test_update_limit_order_success(self, service_with_provider, mock_trading_provider):
        """Test successful limit order update."""
        result = await service_with_provider.update_limit_order(
            pair_id=1, order_index=0, at_price=50000.0
        )

        assert result["status"] == "updated"
        mock_trading_provider.update_limit_order.assert_called_once_with(1, 0, 50000.0)

    @pytest.mark.asyncio
    async def test_update_limit_order_invalid_price(self, service_with_provider):
        """Test limit order update with invalid price."""
        with pytest.raises(ValueError, match="Order price must be greater than 0"):
            await service_with_provider.update_limit_order(pair_id=1, order_index=0, at_price=0)

    @pytest.mark.asyncio
    async def test_get_pairs_with_provider(self, service_with_provider, mock_trading_provider):
        """Test getting pairs with provider."""
        result = await service_with_provider.get_pairs()

        assert len(result) == 1
        assert result[0]["pair_id"] == 1
        mock_trading_provider.get_pairs.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_pairs_with_category(self, mock_db):
        """Test getting pairs with category filter."""
        with patch("app.services.trading_service.get_provider_router") as mock_router:
            mock_router_instance = MagicMock()
            mock_router_instance._category_provider_map = {"crypto": "lighter"}
            mock_router.return_value = mock_router_instance

            service = TradingService(db=mock_db)

            with patch("app.services.providers.factory.ProviderFactory") as mock_factory:
                mock_provider = MagicMock(spec=BaseTradingProvider)
                mock_provider.get_pairs = AsyncMock(return_value=[{"pair_id": 1}])
                mock_factory.get_trading_provider = AsyncMock(return_value=mock_provider)

                result = await service.get_pairs(category="crypto")

                assert len(result) == 1
                mock_factory.get_trading_provider.assert_called_once_with("lighter")

    @pytest.mark.asyncio
    async def test_get_pairs_all_providers(self, mock_db):
        """Test getting pairs from all providers."""
        with patch("app.services.trading_service.get_provider_router") as mock_router:
            mock_router_instance = MagicMock()
            mock_router.return_value = mock_router_instance

            service = TradingService(db=mock_db)

            with patch("app.services.providers.factory.ProviderFactory") as mock_factory:
                mock_provider = MagicMock(spec=BaseTradingProvider)
                mock_provider.get_pairs = AsyncMock(return_value=[{"pair_id": 1}])
                mock_factory.get_trading_provider = AsyncMock(return_value=mock_provider)

                result = await service.get_pairs()

                assert len(result) >= 1
                # Should call for both lighter and ostium
                assert mock_factory.get_trading_provider.call_count >= 1

