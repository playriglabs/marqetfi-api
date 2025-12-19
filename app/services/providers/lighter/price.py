"""Lighter price provider implementation."""

from typing import Any

from app.config.providers.lighter import LighterConfig
from app.services.providers.base import BasePriceProvider
from app.services.providers.exceptions import PriceProviderError
from app.services.providers.lighter.base import LighterService

# Optional import for lighter SDK
try:
    import lighter
except ImportError:
    lighter = None  # type: ignore


class LighterPriceProvider(BasePriceProvider):
    """Lighter implementation of PriceProvider."""

    def __init__(self, config: LighterConfig):
        """Initialize Lighter price provider."""
        super().__init__("lighter-price")
        self.lighter_service = LighterService(config)

    async def initialize(self) -> None:
        """Initialize the provider."""
        await self.lighter_service.initialize()

    async def health_check(self) -> bool:
        """Check provider health."""
        return await self.lighter_service.health_check()

    async def get_price(self, asset: str, quote: str) -> tuple[float, int, str]:
        """Get current price for an asset."""
        try:
            if lighter is None:
                raise ImportError(
                    "lighter-python is not installed. Install with: "
                    "pip install git+https://github.com/elliottech/lighter-python.git"
                )

            await self.lighter_service.initialize()

            import asyncio

            # Get market data from Lighter
            # This is a placeholder - adjust based on actual API
            market_api = lighter.MarketApi(self.lighter_service.client)  # type: ignore[attr-defined]

            # Get ticker/price for the market
            ticker = await asyncio.to_thread(market_api.get_ticker, market=f"{asset}/{quote}")

            # Extract price, timestamp, and source
            price = float(ticker.get("last_price", 0))
            timestamp = int(ticker.get("timestamp", 0))
            source = "lighter"

            return (price, timestamp, source)
        except Exception as e:
            error = self.lighter_service.handle_service_error(e, "get_price")
            raise PriceProviderError(str(error), service_name=self.service_name) from e

    async def get_prices(self, assets: list[tuple[str, str]]) -> dict[str, tuple[float, int, str]]:
        """Get prices for multiple assets."""
        try:
            await self.lighter_service.initialize()

            import asyncio

            import lighter

            results: dict[str, tuple[float, int, str]] = {}
            market_api = lighter.MarketApi(self.lighter_service.client)  # type: ignore[attr-defined]

            # Fetch prices concurrently
            tasks = [
                asyncio.to_thread(market_api.get_ticker, market=f"{asset}/{quote}")
                for asset, quote in assets
            ]

            tickers = await asyncio.gather(*tasks, return_exceptions=True)

            for (asset, quote), ticker_data in zip(assets, tickers, strict=False):
                key = f"{asset}/{quote}"
                if isinstance(ticker_data, Exception):
                    error = self.lighter_service.handle_service_error(
                        ticker_data, f"get_price({key})"
                    )
                    continue

                if not isinstance(ticker_data, dict):
                    continue

                price = float(ticker_data.get("last_price", 0))
                timestamp = int(ticker_data.get("timestamp", 0))
                results[key] = (price, timestamp, "lighter")

            return results
        except Exception as e:
            error = self.lighter_service.handle_service_error(e, "get_prices")
            raise PriceProviderError(str(error), service_name=self.service_name) from e

    async def get_pairs(self) -> list[dict[str, Any]]:
        """Get all available trading pairs."""
        try:
            await self.lighter_service.initialize()

            import asyncio

            import lighter

            market_api = lighter.MarketApi(self.lighter_service.client)  # type: ignore[attr-defined]
            markets = await asyncio.to_thread(market_api.get_markets)

            return list(markets) if markets else []
        except Exception as e:
            error = self.lighter_service.handle_service_error(e, "get_pairs")
            raise PriceProviderError(str(error), service_name=self.service_name) from e
