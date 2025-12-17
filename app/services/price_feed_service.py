"""Price feed service for market data."""

from typing import Any

from app.core.cache import cache_manager
from app.services.providers.base import BasePriceProvider
from app.services.providers.pair_parser import format_pair, parse_pair
from app.services.providers.router import get_provider_router


class PriceFeedService:
    """Service for price feed operations."""

    def __init__(self, price_provider: BasePriceProvider | None = None):
        """Initialize price feed service.

        If price_provider is None, uses ProviderRouter for multi-provider support.
        """
        self.price_provider = price_provider
        self.router = get_provider_router() if price_provider is None else None
        self.cache_ttl = 60  # Cache prices for 60 seconds

    async def get_price(
        self, asset: str, quote: str, use_cache: bool = True
    ) -> tuple[float, int, str]:
        """Get current price for an asset (legacy method)."""
        cache_key = f"price:{asset}:{quote}"

        if use_cache:
            cached = await cache_manager.get(cache_key)
            if cached:
                return tuple(cached)  # type: ignore

        # Get provider based on asset
        if self.router:
            provider = await self.router.get_price_provider(asset)
        else:
            if self.price_provider is None:
                raise ValueError("Price provider not configured")
            provider = self.price_provider

        price, timestamp, source = await provider.get_price(asset, quote)

        if use_cache:
            await cache_manager.set(cache_key, [price, timestamp, source], expire=self.cache_ttl)

        return (price, timestamp, source)

    async def get_price_by_pair(
        self, pair: str, use_cache: bool = True
    ) -> tuple[float, int, str, str, str]:
        """Get current price for a trading pair in combined format.

        Args:
            pair: Trading pair in combined format (e.g., BTCUSDT, EURUSD)
            use_cache: Whether to use cache

        Returns:
            Tuple of (price, timestamp, source, asset, quote)
        """
        asset, quote = parse_pair(pair)
        cache_key = f"price:{pair}"

        if use_cache:
            cached = await cache_manager.get(cache_key)
            if cached:
                return tuple(cached)  # type: ignore

        # Get provider based on asset
        if self.router:
            provider = await self.router.get_price_provider(asset)
        else:
            if self.price_provider is None:
                raise ValueError("Price provider not configured")
            provider = self.price_provider

        price, timestamp, source = await provider.get_price(asset, quote)

        result = (price, timestamp, source, asset, quote)

        if use_cache:
            await cache_manager.set(cache_key, list(result), expire=self.cache_ttl)

        return result

    async def get_prices(
        self, assets: list[tuple[str, str]], use_cache: bool = True
    ) -> dict[str, tuple[float, int, str]]:
        """Get prices for multiple assets (legacy method)."""
        results: dict[str, tuple[float, int, str]] = {}

        # Check cache first
        if use_cache:
            for asset, quote in assets:
                pair = format_pair(asset, quote)
                cache_key = f"price:{pair}"
                cached = await cache_manager.get(cache_key)
                if cached:
                    results[pair] = tuple(cached[:3])  # type: ignore

        # Get missing prices from provider
        missing = [
            (asset, quote) for asset, quote in assets if format_pair(asset, quote) not in results
        ]

        if missing:
            if self.router:
                # Group by provider and fetch from appropriate providers
                provider_groups: dict[str, list[tuple[str, str]]] = {}
                for asset, quote in missing:
                    provider_name = self.router.get_provider_for_asset(asset)
                    if provider_name not in provider_groups:
                        provider_groups[provider_name] = []
                    provider_groups[provider_name].append((asset, quote))

                # Fetch from each provider
                for _provider_name, assets_list in provider_groups.items():
                    provider = await self.router.get_price_provider(assets_list[0][0])
                    provider_prices = await provider.get_prices(assets_list)

                    # Cache and add to results
                    for key, price_data in provider_prices.items():
                        # Provider returns "asset/quote" format, convert to pair
                        if "/" in key:
                            asset, quote = key.split("/", 1)
                            pair = format_pair(asset, quote)
                        else:
                            pair = key
                        results[pair] = price_data[:3]  # Only price, timestamp, source
                        if use_cache:
                            cache_key = f"price:{pair}"
                            await cache_manager.set(
                                cache_key, list(price_data), expire=self.cache_ttl
                            )
            else:
                if self.price_provider is None:
                    raise ValueError("Price provider not configured")
                provider_prices = await self.price_provider.get_prices(missing)

                # Cache and add to results
                for key, price_data in provider_prices.items():
                    if "/" in key:
                        asset, quote = key.split("/", 1)
                        pair = format_pair(asset, quote)
                    else:
                        pair = key
                    results[pair] = price_data[:3]
                    if use_cache:
                        cache_key = f"price:{pair}"
                        await cache_manager.set(cache_key, list(price_data), expire=self.cache_ttl)

        return results

    async def get_prices_by_pairs(
        self, pairs: list[str], use_cache: bool = True
    ) -> dict[str, tuple[float, int, str, str, str]]:
        """Get prices for multiple trading pairs in combined format.

        Args:
            pairs: List of trading pairs in combined format (e.g., ["BTCUSDT", "EURUSD"])
            use_cache: Whether to use cache

        Returns:
            Dictionary mapping pair to (price, timestamp, source, asset, quote)
        """
        results: dict[str, tuple[float, int, str, str, str]] = {}

        # Parse pairs and check cache
        parsed_pairs: list[tuple[str, str, str]] = []  # (pair, asset, quote)
        for pair in pairs:
            try:
                asset, quote = parse_pair(pair)
                parsed_pairs.append((pair, asset, quote))

                if use_cache:
                    cache_key = f"price:{pair}"
                    cached = await cache_manager.get(cache_key)
                    if cached:
                        results[pair] = tuple(cached)  # type: ignore
            except ValueError:
                continue

        # Get missing prices
        missing = [
            (pair, asset, quote) for pair, asset, quote in parsed_pairs if pair not in results
        ]

        if missing:
            if self.router:
                # Group by provider
                provider_groups: dict[str, list[tuple[str, str]]] = {}
                for _pair, asset, quote in missing:
                    provider_name = self.router.get_provider_for_asset(asset)
                    if provider_name not in provider_groups:
                        provider_groups[provider_name] = []
                    provider_groups[provider_name].append((asset, quote))

                # Fetch from each provider
                for _provider_name, assets_list in provider_groups.items():
                    provider = await self.router.get_price_provider(assets_list[0][0])
                    provider_prices = await provider.get_prices(assets_list)

                    # Map back to pairs - create lookup for (asset, quote) -> pair
                    asset_quote_to_pair = {
                        (_asset, _quote): _pair for _pair, _asset, _quote in missing
                    }

                    # Process provider results
                    for key, price_data in provider_prices.items():
                        # Provider returns "asset/quote" format
                        if "/" in key:
                            asset, quote = key.split("/", 1)
                            pair_key = (asset, quote)
                        else:
                            # Try to parse as combined pair
                            try:
                                asset, quote = parse_pair(key)
                                pair_key = (asset, quote)
                            except ValueError:
                                continue

                        if pair_key in asset_quote_to_pair:
                            pair = asset_quote_to_pair[pair_key]
                            result = (price_data[0], price_data[1], price_data[2], asset, quote)
                            results[pair] = result
                            if use_cache:
                                cache_key = f"price:{pair}"
                                await cache_manager.set(
                                    cache_key, list(result), expire=self.cache_ttl
                                )
            else:
                # Single provider
                if self.price_provider is None:
                    raise ValueError("Price provider not configured")
                assets_list = [(asset, quote) for _, asset, quote in missing]
                provider_prices = await self.price_provider.get_prices(assets_list)

                for pair, asset, quote in missing:
                    key = f"{asset}/{quote}"
                    if key in provider_prices:
                        price_data = provider_prices[key]
                        result = (price_data[0], price_data[1], price_data[2], asset, quote)
                        results[pair] = result
                        if use_cache:
                            cache_key = f"price:{pair}"
                            await cache_manager.set(cache_key, list(result), expire=self.cache_ttl)

        return results

    async def get_pairs(self, category: str | None = None) -> list[dict[str, Any]]:
        """Get all available trading pairs.

        Args:
            category: Optional category filter (crypto, forex, indices, commodities)
        """
        if self.router and category:
            # Get provider for category
            provider_name = self.router._category_provider_map.get(category.lower(), "ostium")
            from app.services.providers.factory import ProviderFactory

            provider = await ProviderFactory.get_price_provider(provider_name)
            return await provider.get_pairs()
        elif self.router:
            # Get pairs from all providers
            all_pairs = []
            for provider_name in ["lighter", "ostium"]:
                try:
                    from app.services.providers.factory import ProviderFactory

                    provider = await ProviderFactory.get_price_provider(provider_name)
                    pairs = await provider.get_pairs()
                    # Tag pairs with provider
                    for pair in pairs:
                        pair["provider"] = provider_name
                    all_pairs.extend(pairs)
                except Exception:
                    continue
            return all_pairs
        else:
            if self.price_provider is None:
                raise ValueError("Price provider not configured")
            return await self.price_provider.get_pairs()
