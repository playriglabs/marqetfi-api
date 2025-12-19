"""Wallet provider interfaces and implementations."""

# Import providers to trigger auto-registration
try:
    from app.services.wallet_providers import privy  # noqa: F401
except ImportError:
    # Privy provider not available
    pass

try:
    from app.services.wallet_providers import dynamic  # noqa: F401
except ImportError:
    # Dynamic provider not available
    pass

from app.services.wallet_providers.base import BaseWalletProvider
from app.services.wallet_providers.exceptions import (
    WalletCreationError,
    WalletNotFoundError,
    WalletProviderError,
    WalletProviderUnavailableError,
    WalletSigningError,
)
from app.services.wallet_providers.factory import WalletProviderFactory
from app.services.wallet_providers.registry import WalletProviderRegistry

__all__: list[str] = [
    "BaseWalletProvider",
    "WalletProviderFactory",
    "WalletProviderRegistry",
    "WalletProviderError",
    "WalletCreationError",
    "WalletNotFoundError",
    "WalletSigningError",
    "WalletProviderUnavailableError",
]
