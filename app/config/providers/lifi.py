"""LI-FI provider configuration."""

from pydantic import Field

from app.config.providers.base import BaseProviderConfig


class LifiConfig(BaseProviderConfig):
    """LI-FI provider configuration."""

    api_url: str = Field(
        default="https://li.xyz/v1",
        description="LI-FI API base URL",
    )
    api_key: str | None = Field(
        default=None, description="API key for authentication (if required)"
    )
    timeout: int = Field(default=30, description="Request timeout in seconds")
    retry_attempts: int = Field(
        default=3, description="Number of retry attempts for failed requests"
    )
    retry_delay: float = Field(default=1.0, description="Delay between retry attempts in seconds")
