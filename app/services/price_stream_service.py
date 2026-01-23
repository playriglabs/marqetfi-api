"""Price stream service for real-time price subscriptions."""

import asyncio
from collections.abc import Awaitable, Callable

from app.core.logging import logger
from app.services.price_feed_service import PriceFeedService


class PriceStreamService:
    """Service for real-time price streaming with pub/sub pattern."""

    POLL_INTERVAL = 1.0

    def __init__(self, price_feed_service: PriceFeedService | None = None):
        """Initialize price stream service.

        Args:
            price_feed_service: Optional existing PriceFeedService instance
        """
        self.price_feed = price_feed_service or PriceFeedService()
        self.subscribers: dict[str, list[Callable[[float, int, str], Awaitable[None]]]] = {}
        self._stream_task: asyncio.Task[None] | None = None
        self._running = False

    async def subscribe(
        self,
        pair: str,
        callback: Callable[[float, int, str], Awaitable[None]],
    ) -> None:
        """Subscribe to price updates for a trading pair.

        Args:
            pair: Trading pair (e.g., 'BTC-USD')
            callback: Async callback function(price, timestamp, source)
        """
        if pair not in self.subscribers:
            self.subscribers[pair] = []

        if callback not in self.subscribers[pair]:
            self.subscribers[pair].append(callback)
            logger.info(
                f"Price stream: subscribed to {pair}, total subscribers: {len(self.subscribers[pair])}"
            )

    async def unsubscribe(
        self,
        pair: str,
        callback: Callable[[float, int, str], Awaitable[None]],
    ) -> None:
        """Unsubscribe from price updates.

        Args:
            pair: Trading pair
            callback: Callback to remove
        """
        if pair in self.subscribers:
            if callback in self.subscribers[pair]:
                self.subscribers[pair].remove(callback)
                logger.info(f"Price stream: unsubscribed from {pair}")

            if not self.subscribers[pair]:
                del self.subscribers[pair]
                logger.info(f"Price stream: no more subscribers for {pair}")

    async def unsubscribe_all(self, pair: str) -> None:
        """Unsubscribe all callbacks from a pair.

        Args:
            pair: Trading pair
        """
        if pair in self.subscribers:
            count = len(self.subscribers[pair])
            del self.subscribers[pair]
            logger.info(f"Price stream: removed all {count} subscribers from {pair}")

    async def start_stream(self) -> None:
        """Start background price streaming task."""
        if self._running:
            logger.warning("Price stream already running")
            return

        self._running = True
        self._stream_task = asyncio.create_task(self._stream_loop())
        logger.info("Price stream started")

    async def stop_stream(self) -> None:
        """Stop background price streaming task."""
        if not self._running:
            return

        self._running = False
        if self._stream_task:
            self._stream_task.cancel()
            try:
                await self._stream_task
            except asyncio.CancelledError:
                pass
        logger.info("Price stream stopped")

    async def _stream_loop(self) -> None:
        """Background task that polls prices and notifies subscribers."""
        while self._running:
            try:
                pairs = list(self.subscribers.keys())

                for pair in pairs:
                    if pair not in self.subscribers:
                        continue

                    try:
                        (
                            price,
                            timestamp,
                            source,
                            _asset,
                            _quote,
                        ) = await self.price_feed.get_price_by_pair(pair)

                        callbacks = self.subscribers.get(pair, []).copy()

                        for callback in callbacks:
                            try:
                                await callback(price, timestamp, source)
                            except Exception as e:
                                logger.error(f"Price stream: callback error for {pair}: {e}")

                    except Exception as e:
                        logger.error(f"Price stream: failed to fetch price for {pair}: {e}")

                await asyncio.sleep(self.POLL_INTERVAL)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Price stream: unexpected error in loop: {e}")
                await asyncio.sleep(self.POLL_INTERVAL)

    def get_subscriber_count(self, pair: str | None = None) -> int:
        """Get subscriber count for pair or all pairs.

        Args:
            pair: Trading pair, or None for all pairs

        Returns:
            Number of subscribers
        """
        if pair:
            return len(self.subscribers.get(pair, []))
        return sum(len(callbacks) for callbacks in self.subscribers.values())

    def get_active_pairs(self) -> list[str]:
        """Get list of pairs with active subscriptions.

        Returns:
            List of trading pairs
        """
        return list(self.subscribers.keys())

    @property
    def is_running(self) -> bool:
        """Check if stream is running.

        Returns:
            True if stream is running
        """
        return self._running


price_stream_service = PriceStreamService()
