"""Price feed service for market data."""

from typing import Any

from app.core.cache import cache_manager
from app.services.providers.base import BasePriceProvider


class PriceFeedService:
    """Service for price feed operations."""

    def __init__(self, price_provider: BasePriceProvider):
        """Initialize price feed service."""
        self.price_provider = price_provider
        self.cache_ttl = 60  # Cache prices for 60 seconds

    async def get_price(
        self, asset: str, quote: str, use_cache: bool = True
    ) -> tuple[float, int, str]:
        """Get current price for an asset."""
        cache_key = f"price:{asset}:{quote}"

        if use_cache:
            cached = await cache_manager.get(cache_key)
            if cached:
                return tuple(cached)  # type: ignore

        price, timestamp, source = await self.price_provider.get_price(asset, quote)

        if use_cache:
            await cache_manager.set(
                cache_key, [price, timestamp, source], expire=self.cache_ttl
            )

        return (price, timestamp, source)

    async def get_prices(
        self, assets: list[tuple[str, str]], use_cache: bool = True
    ) -> dict[str, tuple[float, int, str]]:
        """Get prices for multiple assets."""
        results: dict[str, tuple[float, int, str]] = {}

        # Check cache first
        if use_cache:
            for asset, quote in assets:
                cache_key = f"price:{asset}:{quote}"
                cached = await cache_manager.get(cache_key)
                if cached:
                    results[f"{asset}/{quote}"] = tuple(cached)  # type: ignore

        # Get missing prices from provider
        missing = [
            (asset, quote)
            for asset, quote in assets
            if f"{asset}/{quote}" not in results
        ]

        if missing:
            provider_prices = await self.price_provider.get_prices(missing)

            # Cache and add to results
            for key, price_data in provider_prices.items():
                results[key] = price_data
                if use_cache:
                    # Extract asset and quote from key (format: "asset/quote")
                    asset, quote = key.split("/", 1)
                    cache_key = f"price:{asset}:{quote}"
                    await cache_manager.set(
                        cache_key, list(price_data), expire=self.cache_ttl
                    )

        return results

    async def get_pairs(self) -> list[dict[str, Any]]:
        """Get all available trading pairs."""
        return await self.price_provider.get_pairs()

