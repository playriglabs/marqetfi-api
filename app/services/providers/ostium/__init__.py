"""Ostium provider implementations."""

from app.services.providers.ostium.base import OstiumService
from app.services.providers.ostium.price import OstiumPriceProvider
from app.services.providers.ostium.settlement import OstiumSettlementProvider
from app.services.providers.ostium.trading import OstiumTradingProvider
from app.services.providers.registry import ProviderRegistry

# Auto-register Ostium providers
ProviderRegistry.register_trading_provider("ostium", OstiumTradingProvider)
ProviderRegistry.register_price_provider("ostium", OstiumPriceProvider)
ProviderRegistry.register_settlement_provider("ostium", OstiumSettlementProvider)

__all__ = [
    "OstiumService",
    "OstiumTradingProvider",
    "OstiumPriceProvider",
    "OstiumSettlementProvider",
]

