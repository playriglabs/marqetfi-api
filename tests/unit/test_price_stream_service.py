"""Test PriceStreamService."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.price_stream_service import PriceStreamService


class TestPriceStreamService:
    """Test PriceStreamService class."""

    @pytest.fixture
    def mock_price_feed(self):
        """Create mock price feed service."""
        feed = MagicMock()
        feed.get_price_by_pair = AsyncMock(return_value=(50000.0, 1234567890, "provider"))
        return feed

    @pytest.fixture
    def service(self, mock_price_feed):
        """Create PriceStreamService instance."""
        return PriceStreamService(price_feed_service=mock_price_feed)

    @pytest.mark.asyncio
    async def test_subscribe(self, service):
        """Test subscribing to price updates."""
        callback = AsyncMock()

        await service.subscribe("BTC-USD", callback)

        assert "BTC-USD" in service.subscribers
        assert callback in service.subscribers["BTC-USD"]
        assert service.get_subscriber_count("BTC-USD") == 1

    @pytest.mark.asyncio
    async def test_subscribe_multiple_callbacks(self, service):
        """Test multiple callbacks for same pair."""
        callback1 = AsyncMock()
        callback2 = AsyncMock()

        await service.subscribe("BTC-USD", callback1)
        await service.subscribe("BTC-USD", callback2)

        assert service.get_subscriber_count("BTC-USD") == 2

    @pytest.mark.asyncio
    async def test_subscribe_duplicate_ignored(self, service):
        """Test subscribing same callback twice is ignored."""
        callback = AsyncMock()

        await service.subscribe("BTC-USD", callback)
        await service.subscribe("BTC-USD", callback)

        assert service.get_subscriber_count("BTC-USD") == 1

    @pytest.mark.asyncio
    async def test_unsubscribe(self, service):
        """Test unsubscribing from price updates."""
        callback = AsyncMock()

        await service.subscribe("BTC-USD", callback)
        await service.unsubscribe("BTC-USD", callback)

        assert "BTC-USD" not in service.subscribers

    @pytest.mark.asyncio
    async def test_unsubscribe_all(self, service):
        """Test unsubscribing all callbacks from pair."""
        callback1 = AsyncMock()
        callback2 = AsyncMock()

        await service.subscribe("BTC-USD", callback1)
        await service.subscribe("BTC-USD", callback2)
        await service.unsubscribe_all("BTC-USD")

        assert "BTC-USD" not in service.subscribers

    @pytest.mark.asyncio
    async def test_get_active_pairs(self, service):
        """Test getting active trading pairs."""
        await service.subscribe("BTC-USD", AsyncMock())
        await service.subscribe("ETH-USD", AsyncMock())

        pairs = service.get_active_pairs()

        assert "BTC-USD" in pairs
        assert "ETH-USD" in pairs
        assert len(pairs) == 2

    @pytest.mark.asyncio
    async def test_get_subscriber_count_all(self, service):
        """Test getting total subscriber count."""
        await service.subscribe("BTC-USD", AsyncMock())
        await service.subscribe("BTC-USD", AsyncMock())
        await service.subscribe("ETH-USD", AsyncMock())

        total = service.get_subscriber_count()

        assert total == 3

    @pytest.mark.asyncio
    async def test_is_running_property(self, service):
        """Test is_running property."""
        assert service.is_running is False

        await service.start_stream()
        assert service.is_running is True

        await service.stop_stream()
        assert service.is_running is False

    @pytest.mark.asyncio
    async def test_start_stop_stream(self, service):
        """Test starting and stopping stream."""
        await service.start_stream()
        assert service._running is True
        assert service._stream_task is not None

        await service.stop_stream()
        assert service._running is False

    @pytest.mark.asyncio
    async def test_stream_notifies_subscribers(self, service, mock_price_feed):
        """Test stream notifies subscribers with price updates."""
        callback = AsyncMock()
        await service.subscribe("BTC-USD", callback)

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            mock_sleep.side_effect = [None, asyncio.CancelledError()]
            await service.start_stream()
            await asyncio.sleep(0.1)
            await service.stop_stream()

        mock_price_feed.get_price_by_pair.assert_called()
