"""Privy wallet provider implementation."""

from app.services.wallet_providers.privy.provider import PrivyWalletProvider
from app.services.wallet_providers.registry import WalletProviderRegistry

# Auto-register provider
WalletProviderRegistry.register("privy", PrivyWalletProvider)

__all__ = ["PrivyWalletProvider"]
