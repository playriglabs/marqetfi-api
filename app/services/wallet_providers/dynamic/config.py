"""Dynamic wallet provider configuration."""

from pydantic import Field

from app.config.providers.base import BaseProviderConfig


class DynamicWalletConfig(BaseProviderConfig):
    """Dynamic wallet provider configuration."""

    api_key: str = Field(default="", description="Dynamic API key")
    api_secret: str = Field(default="", description="Dynamic API secret")
    api_url: str = Field(
        default="https://api.dynamic.xyz",
        description="Dynamic API base URL",
    )
    environment: str = Field(
        default="production",
        description="Dynamic environment (production/sandbox)",
    )
