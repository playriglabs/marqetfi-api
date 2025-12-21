"""Privy authentication provider implementation."""

from app.services.providers.privy.provider import PrivyAuthProvider
from app.services.providers.registry import ProviderRegistry

# Auto-register Privy provider
ProviderRegistry.register_auth_provider("privy", PrivyAuthProvider)

__all__ = ["PrivyAuthProvider"]
