"""Dynamic wallet provider implementation."""

from app.services.wallet_providers.dynamic.provider import DynamicWalletProvider
from app.services.wallet_providers.registry import WalletProviderRegistry

# Auto-register provider
WalletProviderRegistry.register("dynamic", DynamicWalletProvider)

__all__ = ["DynamicWalletProvider"]
