"""Provider router for multi-provider support."""

from app.services.providers.base import (
    BasePriceProvider,
    BaseSettlementProvider,
    BaseTradingProvider,
)
from app.services.providers.factory import ProviderFactory


class ProviderRouter:
    """Router for selecting providers based on asset type or category."""

    def __init__(self) -> None:
        """Initialize provider router."""
        self._asset_category_map: dict[str, str] = {}  # asset -> category
        self._category_provider_map: dict[str, str] = {}  # category -> provider
        self._asset_provider_map: dict[str, str] = {}  # asset -> provider (direct override)

    def configure_asset_category(
        self, asset: str, category: str, provider: str | None = None
    ) -> None:
        """Configure asset category and optional provider."""
        self._asset_category_map[asset.upper()] = category.lower()
        if provider:
            self._asset_provider_map[asset.upper()] = provider.lower()

    def configure_category_provider(self, category: str, provider: str) -> None:
        """Configure default provider for a category."""
        self._category_provider_map[category.lower()] = provider.lower()

    def configure_asset_provider(self, asset: str, provider: str) -> None:
        """Configure direct asset-to-provider mapping (overrides category)."""
        self._asset_provider_map[asset.upper()] = provider.lower()

    def get_asset_category(self, asset: str) -> str:
        """Get category for an asset."""
        asset_upper = asset.upper()

        # Check direct mapping first
        if asset_upper in self._asset_provider_map:
            # Infer category from provider if needed
            provider = self._asset_provider_map[asset_upper]
            if provider == "lighter":
                return "crypto"
            elif provider == "ostium":
                # Could be any trad-fi category
                return "tradfi"

        # Check category map
        if asset_upper in self._asset_category_map:
            return self._asset_category_map[asset_upper]

        # Default: try to infer from common patterns
        crypto_assets = {"BTC", "ETH", "SOL", "AVAX", "MATIC", "ARB", "OP"}
        if asset_upper in crypto_assets:
            return "crypto"

        # Default to tradfi for unknown assets
        return "tradfi"

    def get_provider_for_asset(self, asset: str) -> str:
        """Get provider name for an asset."""
        asset_upper = asset.upper()

        # Direct mapping takes precedence
        if asset_upper in self._asset_provider_map:
            return self._asset_provider_map[asset_upper]

        # Get category and find provider
        category = self.get_asset_category(asset_upper)
        if category in self._category_provider_map:
            return self._category_provider_map[category]

        # Default fallback
        return "ostium"

    def get_provider_for_asset_type(self, asset_type: int) -> str:
        """Get provider for numeric asset type (Ostium format)."""
        # Ostium asset types: 0=BTC, 1=ETH, etc.
        # Map crypto asset types to lighter, others to ostium
        # This is a placeholder - adjust based on actual asset type mapping
        crypto_asset_types = {0, 1}  # BTC, ETH typically
        if asset_type in crypto_asset_types:
            return "lighter"
        return "ostium"

    async def get_trading_provider(
        self, asset: str | None = None, asset_type: int | None = None
    ) -> BaseTradingProvider:
        """Get trading provider for asset or asset type."""
        if asset:
            provider_name = self.get_provider_for_asset(asset)
        elif asset_type is not None:
            provider_name = self.get_provider_for_asset_type(asset_type)
        else:
            # Fallback to default
            from app.config import get_settings

            settings = get_settings()
            provider_name = getattr(settings, "TRADING_PROVIDER", "ostium")

        return await ProviderFactory.get_trading_provider(provider_name)

    async def get_price_provider(self, asset: str) -> BasePriceProvider:
        """Get price provider for an asset."""
        provider_name = self.get_provider_for_asset(asset)
        return await ProviderFactory.get_price_provider(provider_name)

    async def get_settlement_provider(
        self, asset: str | None = None, asset_type: int | None = None
    ) -> BaseSettlementProvider:
        """Get settlement provider for asset or asset type."""
        if asset:
            provider_name = self.get_provider_for_asset(asset)
        elif asset_type is not None:
            provider_name = self.get_provider_for_asset_type(asset_type)
        else:
            from app.config import get_settings

            settings = get_settings()
            provider_name = getattr(settings, "SETTLEMENT_PROVIDER", "ostium")

        return await ProviderFactory.get_settlement_provider(provider_name)


# Global router instance
_provider_router: ProviderRouter | None = None


def get_provider_router() -> ProviderRouter:
    """Get or create global provider router."""
    global _provider_router
    if _provider_router is None:
        _provider_router = ProviderRouter()
        _initialize_default_routing(_provider_router)
    return _provider_router


def _initialize_default_routing(router: ProviderRouter) -> None:
    """Initialize default routing configuration."""
    from app.config import get_settings

    settings = get_settings()

    # Configure category-to-provider mapping
    router.configure_category_provider("crypto", "lighter")
    router.configure_category_provider("forex", "ostium")
    router.configure_category_provider("indices", "ostium")
    router.configure_category_provider("commodities", "ostium")
    router.configure_category_provider("tradfi", "ostium")

    # Configure common crypto assets
    crypto_assets = ["BTC", "ETH", "SOL", "AVAX", "MATIC", "ARB", "OP", "LINK", "UNI"]
    for asset in crypto_assets:
        router.configure_asset_category(asset, "crypto", "lighter")

    # Load custom routing from settings if available
    # Format: ASSET_ROUTING={"BTC":"lighter","EURUSD":"ostium"}
    if hasattr(settings, "ASSET_ROUTING"):
        routing = getattr(settings, "ASSET_ROUTING", {})
        if isinstance(routing, dict):
            for asset, provider in routing.items():
                router.configure_asset_provider(asset, provider)
        elif isinstance(routing, str):
            # Support JSON string format from environment variables
            import json

            try:
                routing_dict = json.loads(routing)
                if isinstance(routing_dict, dict):
                    for asset, provider in routing_dict.items():
                        router.configure_asset_provider(asset, provider)
            except json.JSONDecodeError:
                pass
