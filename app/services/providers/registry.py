"""Provider registry for managing provider implementations."""

from app.services.providers.base import (
    BaseAuthProvider,
    BasePriceProvider,
    BaseSettlementProvider,
    BaseSwapProvider,
    BaseTradingProvider,
)


class ProviderRegistry:
    """Registry for provider implementations."""

    _trading_providers: dict[str, type[BaseTradingProvider]] = {}
    _price_providers: dict[str, type[BasePriceProvider]] = {}
    _settlement_providers: dict[str, type[BaseSettlementProvider]] = {}
    _swap_providers: dict[str, type[BaseSwapProvider]] = {}
    _auth_providers: dict[str, type[BaseAuthProvider]] = {}

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

    @classmethod
    def register_swap_provider(cls, name: str, provider_class: type[BaseSwapProvider]) -> None:
        """Register a swap provider."""
        cls._swap_providers[name] = provider_class

    @classmethod
    def get_swap_provider(cls, name: str) -> type[BaseSwapProvider] | None:
        """Get a swap provider class by name."""
        return cls._swap_providers.get(name)

    @classmethod
    def list_swap_providers(cls) -> list[str]:
        """List all registered swap provider names."""
        return list(cls._swap_providers.keys())

    @classmethod
    def register_auth_provider(cls, name: str, provider_class: type[BaseAuthProvider]) -> None:
        """Register an authentication provider."""
        cls._auth_providers[name] = provider_class

    @classmethod
    def get_auth_provider(cls, name: str) -> type[BaseAuthProvider] | None:
        """Get an authentication provider class by name."""
        return cls._auth_providers.get(name)

    @classmethod
    def list_auth_providers(cls) -> list[str]:
        """List all registered authentication provider names."""
        return list(cls._auth_providers.keys())
