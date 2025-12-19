"""Registry for wallet providers."""

from app.services.wallet_providers.base import BaseWalletProvider


class WalletProviderRegistry:
    """Registry for wallet provider implementations."""

    _providers: dict[str, type[BaseWalletProvider]] = {}

    @classmethod
    def register(cls, name: str, provider_class: type[BaseWalletProvider]) -> None:
        """Register a wallet provider.

        Args:
            name: Provider name (e.g., 'privy', 'dynamic')
            provider_class: Provider class implementing BaseWalletProvider
        """
        cls._providers[name] = provider_class

    @classmethod
    def get(cls, name: str) -> type[BaseWalletProvider] | None:
        """Get provider class by name.

        Args:
            name: Provider name

        Returns:
            Provider class or None if not found
        """
        return cls._providers.get(name)

    @classmethod
    def list_providers(cls) -> list[str]:
        """List all registered provider names.

        Returns:
            List of provider names
        """
        return list(cls._providers.keys())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if a provider is registered.

        Args:
            name: Provider name

        Returns:
            True if registered, False otherwise
        """
        return name in cls._providers
