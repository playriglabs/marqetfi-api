"""Auth0 authentication provider configuration."""

from pydantic import Field

from app.config.providers.base import BaseProviderConfig


class Auth0AuthConfig(BaseProviderConfig):
    """Auth0 authentication provider configuration."""

    domain: str = Field(default="", description="Auth0 domain")
    client_id: str = Field(default="", description="Auth0 client ID")
    client_secret: str = Field(default="", description="Auth0 client secret")
    audience: str = Field(default="", description="Auth0 API audience")
    management_client_id: str = Field(default="", description="Auth0 Management API client ID")
    management_client_secret: str = Field(
        default="", description="Auth0 Management API client secret"
    )
    algorithm: str = Field(default="RS256", description="JWT algorithm")
