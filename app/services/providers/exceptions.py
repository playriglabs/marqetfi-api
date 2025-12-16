"""Exceptions for external service providers."""


class ExternalServiceError(Exception):
    """Base exception for all external service errors."""

    def __init__(self, message: str, service_name: str | None = None):
        """Initialize external service error."""
        self.service_name = service_name
        super().__init__(message)


class TradingProviderError(ExternalServiceError):
    """Trading provider specific errors."""

    pass


class PriceProviderError(ExternalServiceError):
    """Price feed provider specific errors."""

    pass


class SettlementProviderError(ExternalServiceError):
    """Settlement provider specific errors."""

    pass


class ServiceUnavailableError(ExternalServiceError):
    """Service connectivity errors."""

    pass

