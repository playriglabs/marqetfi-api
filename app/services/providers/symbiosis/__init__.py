"""Symbiosis provider implementations (placeholder for future)."""

from app.services.providers.registry import ProviderRegistry
from app.services.providers.symbiosis.base import SymbiosisSwapProvider

# Auto-register Symbiosis swap provider (placeholder)
ProviderRegistry.register_swap_provider("symbiosis", SymbiosisSwapProvider)

__all__ = [
    "SymbiosisSwapProvider",
]
