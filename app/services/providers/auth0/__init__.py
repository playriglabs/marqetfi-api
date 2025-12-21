"""Auth0 authentication provider implementation."""

from app.services.providers.auth0.provider import Auth0AuthProvider
from app.services.providers.registry import ProviderRegistry

# Auto-register Auth0 provider
ProviderRegistry.register_auth_provider("auth0", Auth0AuthProvider)

__all__ = ["Auth0AuthProvider"]
