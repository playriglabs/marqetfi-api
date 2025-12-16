"""Base configuration for external service providers."""

from pydantic import Field
from pydantic_settings import BaseSettings


class BaseProviderConfig(BaseSettings):
    """Base configuration for all provider configs."""

    enabled: bool = Field(default=True, description="Whether the provider is enabled")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    retry_delay: float = Field(
        default=1.0, description="Delay between retries in seconds"
    )

    class Config:
        """Pydantic config."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"

