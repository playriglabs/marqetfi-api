"""Provider registry for managing provider implementations."""

from app.services.providers.base import (
    BasePriceProvider,
    BaseSettlementProvider,
    BaseTradingProvider,
)


class ProviderRegistry:
    """Registry for provider implementations."""

    _trading_providers: dict[str, type[BaseTradingProvider]] = {}
    _price_providers: dict[str, type[BasePriceProvider]] = {}
    _settlement_providers: dict[str, type[BaseSettlementProvider]] = {}

    @classmethod
    def register_trading_provider(
        cls, name: str, provider_class: type[BaseTradingProvider]
    ) -> None:
        """Register a trading provider."""
        cls._trading_providers[name] = provider_class

    @classmethod
    def register_price_provider(cls, name: str, provider_class: type[BasePriceProvider]) -> None:
        """Register a price provider."""
        cls._price_providers[name] = provider_class

    @classmethod
    def register_settlement_provider(
        cls, name: str, provider_class: type[BaseSettlementProvider]
    ) -> None:
        """Register a settlement provider."""
        cls._settlement_providers[name] = provider_class

    @classmethod
    def get_trading_provider(cls, name: str) -> type[BaseTradingProvider] | None:
        """Get a trading provider class by name."""
        return cls._trading_providers.get(name)

    @classmethod
    def get_price_provider(cls, name: str) -> type[BasePriceProvider] | None:
        """Get a price provider class by name."""
        return cls._price_providers.get(name)

    @classmethod
    def get_settlement_provider(cls, name: str) -> type[BaseSettlementProvider] | None:
        """Get a settlement provider class by name."""
        return cls._settlement_providers.get(name)

    @classmethod
    def list_trading_providers(cls) -> list[str]:
        """List all registered trading provider names."""
        return list(cls._trading_providers.keys())

    @classmethod
    def list_price_providers(cls) -> list[str]:
        """List all registered price provider names."""
        return list(cls._price_providers.keys())

    @classmethod
    def list_settlement_providers(cls) -> list[str]:
        """List all registered settlement provider names."""
        return list(cls._settlement_providers.keys())
