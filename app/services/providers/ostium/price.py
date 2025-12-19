"""Ostium price provider implementation."""

import time
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

            # SDK returns (price, _) but we need to handle it and provide timestamp/source
            result = await self.ostium_service._execute_with_retry(
                self.ostium_service.sdk.price.get_price,
                "get_price",
                asset,
                quote,
            )

            # Handle both 2-value and 3-value returns for compatibility
            if isinstance(result, tuple):
                if len(result) == 2:
                    price, _ = result
                    # Use current timestamp and source name
                    timestamp = int(time.time())
                    source = "ostium"
                    return (price, timestamp, source)
                elif len(result) == 3:
                    price, timestamp, source = result
                    return (price, timestamp, source)
                else:
                    raise ValueError(f"Unexpected return value from get_price: {result}")
            else:
                # Single value return
                return (float(result), int(time.time()), "ostium")
        except Exception as e:
            error = self.ostium_service.handle_service_error(e, "get_price")
            raise PriceProviderError(str(error), service_name=self.service_name) from e

    async def get_prices(self, assets: list[tuple[str, str]]) -> dict[str, tuple[float, int, str]]:
        """Get prices for multiple assets."""
        try:
            await self.ostium_service.initialize()

            import asyncio

            results: dict[str, tuple[float, int, str]] = {}

            # Fetch prices concurrently with retry logic for each
            async def get_price_with_retry(asset: str, quote: str) -> Any:
                """Get price with retry logic."""
                return await self.ostium_service._execute_with_retry(
                    self.ostium_service.sdk.price.get_price,
                    f"get_price({asset}/{quote})",
                    asset,
                    quote,
                )

            tasks = [get_price_with_retry(asset, quote) for asset, quote in assets]
            prices = await asyncio.gather(*tasks, return_exceptions=True)

            for (asset, quote), price_data in zip(assets, prices, strict=False):
                key = f"{asset}/{quote}"
                if isinstance(price_data, Exception):
                    # Log error but continue with other prices
                    error = self.ostium_service.handle_service_error(
                        price_data, f"get_price({key})"
                    )
                    continue
                if isinstance(price_data, tuple):
                    # Handle both 2-value and 3-value returns
                    if len(price_data) == 2:
                        price, _ = price_data
                        results[key] = (price, int(time.time()), "ostium")
                    elif len(price_data) == 3:
                        results[key] = price_data
                    else:
                        continue
                elif isinstance(price_data, int | float):
                    # Single value return
                    results[key] = (float(price_data), int(time.time()), "ostium")

            return results
        except Exception as e:
            error = self.ostium_service.handle_service_error(e, "get_prices")
            raise PriceProviderError(str(error), service_name=self.service_name) from e

    async def get_pairs(self) -> list[dict[str, Any]]:
        """Get all available trading pairs."""
        try:
            await self.ostium_service.initialize()

            pairs = await self.ostium_service._execute_with_retry(
                self.ostium_service.sdk.subgraph.get_pairs,
                "get_pairs",
            )

            return list(pairs) if pairs else []
        except Exception as e:
            error = self.ostium_service.handle_service_error(e, "get_pairs")
            raise PriceProviderError(str(error), service_name=self.service_name) from e

    async def get_pair_details(self, pair_id: str) -> dict[str, Any]:
        """Get detailed information for a trading pair.

        Args:
            pair_id: The pair ID (from get_pairs() result)

        Returns:
            Dictionary with detailed pair information
        """
        try:
            await self.ostium_service.initialize()

            pair_details = await self.ostium_service._execute_with_retry(
                self.ostium_service.sdk.subgraph.get_pair_details,
                "get_pair_details",
                pair_id,
            )

            return dict(pair_details) if pair_details else {}
        except Exception as e:
            error = self.ostium_service.handle_service_error(e, "get_pair_details")
            raise PriceProviderError(str(error), service_name=self.service_name) from e
