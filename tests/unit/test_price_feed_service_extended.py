"""Extended tests for PriceFeedService methods."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.price_feed_service import PriceFeedService


class TestPriceFeedServiceExtended:
    """Extended tests for PriceFeedService class."""

    @pytest.fixture
    def mock_price_provider(self):
        """Create mock price provider."""
        provider = MagicMock()
        provider.get_price = AsyncMock(return_value=(100.0, 1234567890, "test_source"))
        provider.get_prices = AsyncMock(
            return_value={"BTC/USDT": (100.0, 1234567890, "test_source")}
        )
        provider.get_pairs = AsyncMock(return_value=[{"pair_id": 1, "symbol": "BTCUSDT"}])
        return provider

    @pytest.fixture
    def price_service(self, mock_price_provider):
        """Create PriceFeedService with provider."""
        return PriceFeedService(price_provider=mock_price_provider)

    @pytest.mark.asyncio
    async def test_get_price_no_cache(self, price_service, mock_price_provider):
        """Test getting price without cache."""
        with patch("app.services.price_feed_service.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()

            price, timestamp, source = await price_service.get_price("BTC", "USDT", use_cache=False)

            assert price == 100.0
            assert timestamp == 1234567890
            assert source == "test_source"
            mock_cache.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_price_with_cache_hit(self, price_service):
        """Test getting price with cache hit."""
        with patch("app.services.price_feed_service.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value=[100.0, 1234567890, "cached_source"])

            price, timestamp, source = await price_service.get_price("BTC", "USDT", use_cache=True)

            assert price == 100.0
            assert timestamp == 1234567890
            assert source == "cached_source"

    @pytest.mark.asyncio
    async def test_get_prices_by_pairs_success(self, price_service, mock_price_provider):
        """Test getting prices by pairs successfully."""
        with patch("app.services.price_feed_service.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()

            results = await price_service.get_prices_by_pairs(["BTCUSDT", "ETHUSDT"], use_cache=True)

            assert "BTCUSDT" in results
            assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_get_prices_by_pairs_with_cache(self, price_service):
        """Test getting prices by pairs with cache."""
        with patch("app.services.price_feed_service.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value=[100.0, 1234567890, "cached", "BTC", "USDT"])

            results = await price_service.get_prices_by_pairs(["BTCUSDT"], use_cache=True)

            assert "BTCUSDT" in results

    @pytest.mark.asyncio
    async def test_get_prices_by_pairs_invalid_pair(self, price_service):
        """Test getting prices by pairs with invalid pair."""
        with patch("app.services.price_feed_service.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)

            results = await price_service.get_prices_by_pairs(["INVALID"], use_cache=True)

            assert "INVALID" not in results

    @pytest.mark.asyncio
    async def test_get_pairs_with_category(self, price_service):
        """Test getting pairs with category filter."""
        mock_router = MagicMock()
        mock_router._category_provider_map = {"crypto": "ostium"}
        mock_provider = MagicMock()
        mock_provider.get_pairs = AsyncMock(return_value=[{"pair_id": 1, "symbol": "BTCUSDT"}])

        with patch("app.services.price_feed_service.get_provider_router", return_value=mock_router), patch(
            "app.services.price_feed_service.ProviderFactory.get_price_provider", return_value=mock_provider
        ):
            price_service.router = mock_router

            result = await price_service.get_pairs(category="crypto")

            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_pairs_all_providers(self, price_service):
        """Test getting pairs from all providers."""
        mock_router = MagicMock()
        mock_router._category_provider_map = {}
        mock_provider = MagicMock()
        mock_provider.get_pairs = AsyncMock(return_value=[{"pair_id": 1, "symbol": "BTCUSDT"}])

        with patch("app.services.price_feed_service.get_provider_router", return_value=mock_router), patch(
            "app.services.price_feed_service.ProviderFactory.get_price_provider", return_value=mock_provider
        ):
            price_service.router = mock_router

            result = await price_service.get_pairs()

            assert len(result) >= 1

    @pytest.mark.asyncio
    async def test_get_prices_with_router(self, price_service):
        """Test getting prices with router."""
        mock_router = MagicMock()
        mock_router.get_provider_for_asset = MagicMock(return_value="ostium")
        mock_provider = MagicMock()
        mock_provider.get_prices = AsyncMock(
            return_value={"BTC/USDT": (100.0, 1234567890, "test_source")}
        )
        mock_router.get_price_provider = AsyncMock(return_value=mock_provider)

        with patch("app.services.price_feed_service.cache_manager") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()

            price_service.router = mock_router

            results = await price_service.get_prices([("BTC", "USDT")], use_cache=True)

            assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_get_prices_no_provider(self, price_service):
        """Test getting prices without provider."""
        price_service.price_provider = None
        price_service.router = None

        with pytest.raises(ValueError, match="Price provider not configured"):
            await price_service.get_prices([("BTC", "USDT")])

