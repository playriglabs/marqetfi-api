"""Privy authentication provider configuration."""

from pydantic import Field

from app.config.providers.base import BaseProviderConfig


class PrivyAuthConfig(BaseProviderConfig):
    """Privy authentication provider configuration."""

    app_id: str = Field(default="", description="Privy App ID")
    app_secret: str = Field(default="", description="Privy App Secret")
    environment: str = Field(
        default="production",
        description="Privy environment: 'production' or 'staging'",
    )
    timeout: int = Field(default=30, description="Privy API timeout in seconds")
    retry_attempts: int = Field(default=3, description="Privy retry attempts")
    retry_delay: float = Field(default=1.0, description="Privy retry delay in seconds")
