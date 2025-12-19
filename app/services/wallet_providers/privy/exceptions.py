"""Privy-specific exceptions."""

from app.services.wallet_providers.exceptions import WalletProviderError


class PrivyError(WalletProviderError):
    """Base Privy error."""

    pass


class PrivyAPIError(PrivyError):
    """Privy API error."""

    pass


class PrivyAuthenticationError(PrivyError):
    """Privy authentication error."""

    pass


class PrivyRateLimitError(PrivyError):
    """Privy rate limit error."""

    pass
