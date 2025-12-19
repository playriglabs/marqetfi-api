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

try:
    from app.services.providers.lifi import LifiSwapProvider  # noqa: F401
except ImportError:
    # LI-FI provider not available
    pass

try:
    from app.services.providers.symbiosis import SymbiosisSwapProvider  # noqa: F401
except ImportError:
    # Symbiosis provider not available
    pass

__all__: list[str] = []
