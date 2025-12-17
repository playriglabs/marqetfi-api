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

try:
    from app.services.providers.lighter import (  # noqa: F401
        LighterPriceProvider,
        LighterService,
        LighterSettlementProvider,
        LighterTradingProvider,
    )
except ImportError:
    # Lighter SDK not installed - providers won't be available
    pass

__all__: list[str] = []
