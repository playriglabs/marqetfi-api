"""Test Lighter provider implementations."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config.providers.lighter import LighterConfig
from app.services.providers.lighter.price import LighterPriceProvider
from app.services.providers.lighter.trading import LighterTradingProvider


class TestLighterTradingProvider:
    """Test LighterTradingProvider class."""

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
    async def test_initialize_success(self, trading_provider):
        """Test successful initialization."""
        with patch.object(trading_provider.lighter_service, "initialize", new_callable=AsyncMock):
            await trading_provider.initialize()
            assert trading_provider.lighter_service._initialized is True

    @pytest.mark.asyncio
    async def test_health_check_success(self, trading_provider):
        """Test successful health check."""
        with patch.object(trading_provider.lighter_service, "health_check", return_value=True):
            result = await trading_provider.health_check()
            assert result is True

    @pytest.mark.asyncio
    async def test_open_trade_success(self, trading_provider):
        """Test opening trade successfully."""
        with (
            patch("app.services.providers.lighter.trading.lighter") as mock_lighter,
            patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread,
        ):
            mock_order_api = MagicMock()
            mock_order_api.create_order = MagicMock(return_value={"id": "123"})
            mock_lighter.OrderApi = MagicMock(return_value=mock_order_api)
            mock_to_thread.return_value = {"id": "123"}

            with patch.object(
                trading_provider.lighter_service, "initialize", new_callable=AsyncMock
            ):
                result = await trading_provider.open_trade(
                    collateral=1000.0,
                    leverage=10,
                    asset_type=1,
                    direction=True,
                    order_type="MARKET",
                )

                assert "transaction_hash" in result

    @pytest.mark.asyncio
    async def test_close_trade_success(self, trading_provider):
        """Test closing trade successfully."""
        with (
            patch("app.services.providers.lighter.trading.lighter") as mock_lighter,
            patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread,
        ):
            mock_order_api = MagicMock()
            mock_order_api.cancel_order = MagicMock(return_value={"id": "123"})
            mock_lighter.OrderApi = MagicMock(return_value=mock_order_api)
            mock_to_thread.return_value = {"id": "123"}

            with patch.object(
                trading_provider.lighter_service, "initialize", new_callable=AsyncMock
            ):
                result = await trading_provider.close_trade(pair_id=1, trade_index=0)

                assert result["status"] == "closed"

    @pytest.mark.asyncio
    async def test_get_pairs_success(self, trading_provider):
        """Test getting trading pairs."""
        with (
            patch("app.services.providers.lighter.trading.lighter") as mock_lighter,
            patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread,
        ):
            mock_market_api = MagicMock()
            mock_market_api.get_markets = MagicMock(
                return_value=[{"pair_id": 1, "symbol": "BTCUSDT"}]
            )
            mock_lighter.MarketApi = MagicMock(return_value=mock_market_api)
            mock_to_thread.return_value = [{"pair_id": 1, "symbol": "BTCUSDT"}]

            with patch.object(
                trading_provider.lighter_service, "initialize", new_callable=AsyncMock
            ):
                pairs = await trading_provider.get_pairs()

                assert len(pairs) == 1


class TestLighterPriceProvider:
    """Test LighterPriceProvider class."""

    @pytest.fixture
    def lighter_config(self):
        """Create Lighter config."""
        return LighterConfig(
            enabled=True,
            api_url="https://api.lighter.xyz",
            api_key="test_key",
            private_key="0x123",
            network="mainnet",
        )

    @pytest.fixture
    def price_provider(self, lighter_config):
        """Create LighterPriceProvider instance."""
        return LighterPriceProvider(lighter_config)

    @pytest.mark.asyncio
    async def test_get_price_success(self, price_provider):
        """Test getting price successfully."""
        with (
            patch("app.services.providers.lighter.price.lighter") as mock_lighter,
            patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread,
        ):
            mock_market_api = MagicMock()
            mock_market_api.get_ticker = MagicMock(
                return_value={"last_price": 100.0, "timestamp": 1234567890}
            )
            mock_lighter.MarketApi = MagicMock(return_value=mock_market_api)
            mock_to_thread.return_value = {"last_price": 100.0, "timestamp": 1234567890}

            with patch.object(price_provider.lighter_service, "initialize", new_callable=AsyncMock):
                price, timestamp, source = await price_provider.get_price("BTC", "USDT")

                assert price == 100.0
                assert source == "lighter"

    @pytest.mark.asyncio
    async def test_get_prices_success(self, price_provider):
        """Test getting multiple prices."""
        with (
            patch("app.services.providers.lighter.price.lighter") as mock_lighter,
            patch("asyncio.gather", new_callable=AsyncMock) as mock_gather,
        ):
            mock_market_api = MagicMock()
            mock_lighter.MarketApi = MagicMock(return_value=mock_market_api)
            mock_gather.return_value = [{"last_price": 100.0, "timestamp": 1234567890}]

            with patch.object(price_provider.lighter_service, "initialize", new_callable=AsyncMock):
                result = await price_provider.get_prices([("BTC", "USDT")])

                assert "BTC/USDT" in result

    @pytest.mark.asyncio
    async def test_get_pairs_success(self, price_provider):
        """Test getting trading pairs."""
        with (
            patch("app.services.providers.lighter.price.lighter") as mock_lighter,
            patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread,
        ):
            mock_market_api = MagicMock()
            mock_market_api.get_markets = MagicMock(
                return_value=[{"pair_id": 1, "symbol": "BTCUSDT"}]
            )
            mock_lighter.MarketApi = MagicMock(return_value=mock_market_api)
            mock_to_thread.return_value = [{"pair_id": 1, "symbol": "BTCUSDT"}]

            with patch.object(price_provider.lighter_service, "initialize", new_callable=AsyncMock):
                pairs = await price_provider.get_pairs()

                assert len(pairs) == 1
