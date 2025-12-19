"""LI-FI provider implementations."""

from app.services.providers.lifi.base import LifiSwapProvider
from app.services.providers.registry import ProviderRegistry

# Auto-register LI-FI swap provider
ProviderRegistry.register_swap_provider("lifi", LifiSwapProvider)

__all__ = [
    "LifiSwapProvider",
]
