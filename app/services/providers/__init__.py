"""Provider interfaces and implementations."""

# Import providers to trigger auto-registration
try:
    from app.services.providers.ostium import (  # noqa: F401
        OstiumPriceProvider,
        OstiumService,
        OstiumSettlementProvider,
        OstiumTradingProvider,
    )
except ImportError:
    # Ostium SDK not installed - providers won't be available
    pass

__all__ = []
