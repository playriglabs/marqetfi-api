"""Exceptions for wallet providers."""

from app.services.providers.exceptions import ExternalServiceError


class WalletProviderError(ExternalServiceError):
    """Base exception for wallet provider errors."""

    pass


class WalletNotFoundError(WalletProviderError):
    """Wallet not found error."""

    pass


class WalletCreationError(WalletProviderError):
    """Wallet creation error."""

    pass


class WalletSigningError(WalletProviderError):
    """Wallet signing error."""

    pass


class WalletProviderUnavailableError(WalletProviderError):
    """Wallet provider unavailable error."""

    pass
