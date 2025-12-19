"""Privy wallet provider configuration.

Uses the official privy-client SDK: https://pypi.org/project/privy-client/
"""

from pydantic import Field

from app.config.providers.base import BaseProviderConfig


class PrivyWalletConfig(BaseProviderConfig):
    """Privy wallet provider configuration."""

    app_id: str = Field(default="", description="Privy App ID")
    app_secret: str = Field(default="", description="Privy App Secret")
    environment: str = Field(
        default="production",
        description="Privy environment: 'production' or 'staging'",
    )
    use_embedded_wallets: bool = Field(
        default=True,
        description="Use Privy embedded wallets",
    )
