"""Ostium price provider implementation."""

from typing import Any

from app.config.providers.ostium import OstiumConfig
from app.services.providers.base import BasePriceProvider
from app.services.providers.exceptions import PriceProviderError
from app.services.providers.ostium.base import OstiumService


class OstiumPriceProvider(BasePriceProvider):
    """Ostium implementation of PriceProvider."""

    def __init__(self, config: OstiumConfig):
        """Initialize Ostium price provider."""
        super().__init__("ostium-price")
        self.ostium_service = OstiumService(config)

    async def initialize(self) -> None:
        """Initialize the provider."""
        await self.ostium_service.initialize()

    async def health_check(self) -> bool:
        """Check provider health."""
        return await self.ostium_service.health_check()

    async def get_price(self, asset: str, quote: str) -> tuple[float, int, str]:
        """Get current price for an asset."""
        try:
            await self.ostium_service.initialize()

            import asyncio

            price, timestamp, source = await asyncio.to_thread(
                self.ostium_service.sdk.price.get_price, asset, quote
            )

            return (price, timestamp, source)
        except Exception as e:
            error = self.ostium_service.handle_service_error(e, "get_price")
            raise PriceProviderError(str(error), service_name=self.service_name) from e

    async def get_prices(
        self, assets: list[tuple[str, str]]
    ) -> dict[str, tuple[float, int, str]]:
        """Get prices for multiple assets."""
        try:
            await self.ostium_service.initialize()

            import asyncio

            results: dict[str, tuple[float, int, str]] = {}

            # Fetch prices concurrently
            tasks = [
                asyncio.to_thread(
                    self.ostium_service.sdk.price.get_price, asset, quote
                )
                for asset, quote in assets
            ]

            prices = await asyncio.gather(*tasks, return_exceptions=True)

            for (asset, quote), price_data in zip(assets, prices):
                key = f"{asset}/{quote}"
                if isinstance(price_data, Exception):
                    # Log error but continue with other prices
                    error = self.ostium_service.handle_service_error(
                        price_data, f"get_price({key})"
                    )
                    continue
                results[key] = price_data

            return results
        except Exception as e:
            error = self.ostium_service.handle_service_error(e, "get_prices")
            raise PriceProviderError(str(error), service_name=self.service_name) from e

    async def get_pairs(self) -> list[dict[str, Any]]:
        """Get all available trading pairs."""
        try:
            await self.ostium_service.initialize()

            import asyncio

            pairs = await asyncio.to_thread(self.ostium_service.sdk.subgraph.get_pairs)

            return pairs if pairs else []
        except Exception as e:
            error = self.ostium_service.handle_service_error(e, "get_pairs")
            raise PriceProviderError(str(error), service_name=self.service_name) from e

