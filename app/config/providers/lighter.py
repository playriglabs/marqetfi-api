"""Lighter provider configuration."""

from typing import Any

from pydantic import Field

from app.config.providers.base import BaseProviderConfig

# Optional import for lighter SDK
try:
    import lighter
except ImportError:
    lighter = None  # type: ignore[assignment, no-redef]


class LighterConfig(BaseProviderConfig):
    """Lighter provider configuration."""

    api_url: str = Field(
        default="https://api.lighter.xyz",
        description="Lighter API base URL",
    )
    api_key: str | None = Field(
        default=None, description="API key for authentication (if required)"
    )
    private_key: str | None = Field(
        default=None, description="Private key for signing transactions"
    )
    network: str = Field(default="mainnet", description="Network: 'mainnet' or 'testnet'")

    # Token requirements for deposits
    required_token: str = Field(
        default="USDC", description="Required token symbol for deposits (e.g., USDC)"
    )
    required_chain: str = Field(
        default="ethereum", description="Required chain for deposits (e.g., ethereum)"
    )
    required_token_address: str = Field(
        default="",
        description="Required token contract address on the required chain",
    )

    def create_api_client(self) -> Any:
        """Create Lighter API client instance."""

        if lighter is None:
            raise ImportError(
                "lighter-python is not installed. Install with: "
                "pip install git+https://github.com/elliottech/lighter-python.git"
            )

        # Lighter ApiClient doesn't require explicit URL in constructor
        # It uses environment variables or default endpoints
        client = lighter.ApiClient()

        # Set API key if provided
        if self.api_key:
            # Lighter SDK may use different auth mechanism
            # This is a placeholder - adjust based on actual SDK
            pass

        return client
