"""Lighter provider implementations."""

from app.services.providers.lighter.base import LighterService
from app.services.providers.lighter.price import LighterPriceProvider
from app.services.providers.lighter.settlement import LighterSettlementProvider
from app.services.providers.lighter.trading import LighterTradingProvider
from app.services.providers.registry import ProviderRegistry

# Auto-register Lighter providers
ProviderRegistry.register_trading_provider("lighter", LighterTradingProvider)
ProviderRegistry.register_price_provider("lighter", LighterPriceProvider)
ProviderRegistry.register_settlement_provider("lighter", LighterSettlementProvider)

__all__ = [
    "LighterService",
    "LighterTradingProvider",
    "LighterPriceProvider",
    "LighterSettlementProvider",
]
