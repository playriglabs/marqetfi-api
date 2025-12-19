"""Dynamic-specific exceptions."""

from app.services.wallet_providers.exceptions import WalletProviderError


class DynamicError(WalletProviderError):
    """Base Dynamic error."""

    pass


class DynamicAPIError(DynamicError):
    """Dynamic API error."""

    pass


class DynamicAuthenticationError(DynamicError):
    """Dynamic authentication error."""

    pass


class DynamicRateLimitError(DynamicError):
    """Dynamic rate limit error."""

    pass
