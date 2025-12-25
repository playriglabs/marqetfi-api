"""Test PriceFeedService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.price_feed_service import PriceFeedService
from app.services.providers.base import BasePriceProvider


class TestPriceFeedService:
    """Test PriceFeedService class."""

    @pytest.fixture
    def mock_price_provider(self):
        """Create mock price provider."""
        mock_provider = MagicMock(spec=BasePriceProvider)
        mock_provider.get_price = AsyncMock(return_value=(100.0, 1234567890, "test_source"))
        mock_provider.get_prices = AsyncMock(return_value={"BTC/USDT": (100.0, 1234567890, "test")})
        mock_provider.get_pairs = AsyncMock(return_value=[{"pair_id": 1, "symbol": "BTCUSDT"}])
        return mock_provider

    @pytest.fixture
    def service_with_provider(self, mock_price_provider):
        """Create service with provider."""
        return PriceFeedService(price_provider=mock_price_provider)

    @pytest.fixture
    def service_with_router(self):
        """Create service with router."""
        return PriceFeedService()

    @pytest.mark.asyncio
    async def test_get_price_success(self, service_with_provider, mock_price_provider):
        """Test successful price retrieval."""
        price, timestamp, source = await service_with_provider.get_price("BTC", "USDT")

        assert price == 100.0
        assert timestamp == 1234567890
        assert source == "test_source"
        mock_price_provider.get_price.assert_called_once_with("BTC", "USDT")

    @pytest.mark.asyncio
    async def test_get_price_with_cache(self, service_with_provider, mock_price_provider):
        """Test price retrieval with cache."""
        with patch("app.services.price_feed_service.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock(return_value=True)

            await service_with_provider.get_price("BTC", "USDT", use_cache=True)

            mock_cache.get.assert_called_once()
            mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_price_cached(self, service_with_provider):
        """Test retrieving cached price."""
        with patch("app.services.price_feed_service.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value=[99.0, 1234567890, "cached"])

            price, timestamp, source = await service_with_provider.get_price("BTC", "USDT")

            assert price == 99.0
            assert source == "cached"

    @pytest.mark.asyncio
    async def test_get_price_no_provider(self):
        """Test price retrieval without provider."""
        service = PriceFeedService()
        service.router = None

        with pytest.raises(ValueError, match="Price provider not configured"):
            await service.get_price("BTC", "USDT")

    @pytest.mark.asyncio
    async def test_get_price_by_pair_success(self, service_with_provider, mock_price_provider):
        """Test getting price by pair."""
        price, timestamp, source, asset, quote = await service_with_provider.get_price_by_pair(
            "BTCUSDT"
        )

        assert price == 100.0
        assert asset == "BTC"
        assert quote == "USDT"
        mock_price_provider.get_price.assert_called_once_with("BTC", "USDT")

    @pytest.mark.asyncio
    async def test_get_price_by_pair_with_router(self, service_with_router):
        """Test getting price by pair with router."""
        with patch("app.services.price_feed_service.get_provider_router") as mock_router:
            mock_router_instance = MagicMock()
            mock_provider = MagicMock(spec=BasePriceProvider)
            mock_provider.get_price = AsyncMock(return_value=(100.0, 1234567890, "test"))
            mock_router_instance.get_price_provider = AsyncMock(return_value=mock_provider)
            mock_router.return_value = mock_router_instance

            service = PriceFeedService()
            service.router = mock_router_instance

            price, timestamp, source, asset, quote = await service.get_price_by_pair("BTCUSDT")

            assert price == 100.0
            assert asset == "BTC"

    @pytest.mark.asyncio
    async def test_get_prices_success(self, service_with_provider, mock_price_provider):
        """Test getting multiple prices."""
        mock_price_provider.get_prices = AsyncMock(
            return_value={"BTC/USDT": (100.0, 1234567890, "test")}
        )

        results = await service_with_provider.get_prices([("BTC", "USDT")])

        assert "BTCUSDT" in results
        assert results["BTCUSDT"][0] == 100.0

    @pytest.mark.asyncio
    async def test_get_prices_with_cache(self, service_with_provider):
        """Test getting prices with cache."""
        with patch("app.services.price_feed_service.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock(return_value=True)

            mock_provider = MagicMock(spec=BasePriceProvider)
            mock_provider.get_prices = AsyncMock(
                return_value={"BTC/USDT": (100.0, 1234567890, "test")}
            )
            service_with_provider.price_provider = mock_provider

            await service_with_provider.get_prices([("BTC", "USDT")])

            mock_cache.set.assert_called()

    @pytest.mark.asyncio
    async def test_get_prices_by_pairs_success(self, service_with_provider, mock_price_provider):
        """Test getting prices by pairs."""
        mock_price_provider.get_prices = AsyncMock(
            return_value={"BTC/USDT": (100.0, 1234567890, "test")}
        )

        results = await service_with_provider.get_prices_by_pairs(["BTCUSDT"])

        assert "BTCUSDT" in results
        assert results["BTCUSDT"][0] == 100.0
        assert results["BTCUSDT"][3] == "BTC"
        assert results["BTCUSDT"][4] == "USDT"

    @pytest.mark.asyncio
    async def test_get_prices_by_pairs_invalid_pair(self, service_with_provider):
        """Test getting prices with invalid pair."""
        results = await service_with_provider.get_prices_by_pairs(["INVALID"])

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_get_pairs_success(self, service_with_provider, mock_price_provider):
        """Test getting pairs."""
        pairs = await service_with_provider.get_pairs()

        assert len(pairs) == 1
        assert pairs[0]["pair_id"] == 1
        mock_price_provider.get_pairs.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_pairs_with_category(self, service_with_router):
        """Test getting pairs with category."""
        with patch("app.services.price_feed_service.get_provider_router") as mock_router:
            mock_router_instance = MagicMock()
            mock_router_instance._category_provider_map = {"crypto": "lighter"}
            mock_router.return_value = mock_router_instance

            service = PriceFeedService()
            service.router = mock_router_instance

            with patch("app.services.price_feed_service.ProviderFactory") as mock_factory:
                mock_provider = MagicMock(spec=BasePriceProvider)
                mock_provider.get_pairs = AsyncMock(return_value=[{"pair_id": 1}])
                mock_factory.get_price_provider = AsyncMock(return_value=mock_provider)

                pairs = await service.get_pairs(category="crypto")

                assert len(pairs) == 1

    @pytest.mark.asyncio
    async def test_get_pairs_all_providers(self, service_with_router):
        """Test getting pairs from all providers."""
        with patch("app.services.price_feed_service.get_provider_router") as mock_router:
            mock_router_instance = MagicMock()
            mock_router.return_value = mock_router_instance

            service = PriceFeedService()
            service.router = mock_router_instance

            with patch("app.services.price_feed_service.ProviderFactory") as mock_factory:
                mock_provider = MagicMock(spec=BasePriceProvider)
                mock_provider.get_pairs = AsyncMock(return_value=[{"pair_id": 1}])
                mock_factory.get_price_provider = AsyncMock(return_value=mock_provider)

                pairs = await service.get_pairs()

                assert len(pairs) >= 1

