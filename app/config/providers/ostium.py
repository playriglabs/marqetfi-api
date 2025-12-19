"""Ostium provider configuration."""

from ostium_python_sdk import NetworkConfig, OstiumSDK
from pydantic import Field, field_validator

from app.config.providers.base import BaseProviderConfig


class OstiumConfig(BaseProviderConfig):
    """Ostium provider configuration."""

    private_key: str = Field(
        default="", description="Private key for signing (backward compatible)"
    )
    rpc_url: str = Field(default="", description="RPC URL for blockchain connection")
    network: str = Field(default="testnet", description="Network: 'testnet' or 'mainnet'")
    verbose: bool = Field(default=False, description="Enable verbose logging")
    slippage_percentage: float = Field(default=1.0, description="Default slippage percentage")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    retry_attempts: int = Field(
        default=3, description="Number of retry attempts for failed requests"
    )
    retry_delay: float = Field(default=1.0, description="Delay between retry attempts in seconds")

    # Wallet provider support
    wallet_provider: str | None = Field(
        default=None,
        description="Wallet provider name (privy/dynamic) or None for direct private key",
    )
    wallet_provider_id: str | None = Field(
        default=None,
        description="Provider-specific wallet ID (required if wallet_provider is set)",
    )
    use_wallet_provider: bool = Field(
        default=False,
        description="Enable wallet provider integration",
    )
    fallback_to_private_key: bool = Field(
        default=True,
        description="Fall back to private key if wallet provider fails",
    )

    @field_validator("network")
    @classmethod
    def validate_network(cls, v: str) -> str:
        """Validate network value."""
        if v.lower() not in ["testnet", "mainnet"]:
            raise ValueError("Network must be 'testnet' or 'mainnet'")
        return v.lower()

    def get_network_config(self) -> NetworkConfig:
        """Get Ostium network config."""
        if self.network == "testnet":
            return NetworkConfig.testnet()
        return NetworkConfig.mainnet()

    def create_sdk_instance(self) -> OstiumSDK:
        """Create Ostium SDK instance.

        If wallet_provider is configured, the SDK will still be created with a private_key
        (which may be a placeholder), but actual signing will be handled by the wallet provider
        through the OstiumService integration.

        For backward compatibility, if wallet_provider is not set, uses private_key directly.
        """
        # For wallet provider mode, we still need a private key for SDK initialization
        # The actual signing will be handled by WalletSigner in OstiumService
        # If wallet provider is enabled but no private key is available, we'll use a placeholder
        # and rely on the wallet provider for all signing operations

        if not self.rpc_url:
            raise ValueError("Ostium rpc_url is required")

        # Determine which private key to use
        if self.use_wallet_provider and self.wallet_provider:
            # Wallet provider mode: use private key only if available for fallback
            # Otherwise, SDK initialization may need a placeholder
            # Note: Some SDKs may require a non-empty private key even in provider mode
            private_key = self.private_key if self.private_key else "0x" + "0" * 64
        else:
            # Direct private key mode (backward compatible)
            if not self.private_key:
                raise ValueError("Ostium private_key is required when wallet_provider is not used")
            private_key = self.private_key

        config = self.get_network_config()
        return OstiumSDK(
            config,
            private_key,
            self.rpc_url,
            verbose=self.verbose,
        )

    def should_use_wallet_provider(self) -> bool:
        """Check if wallet provider should be used.

        Returns:
            True if wallet provider is enabled and configured, False otherwise
        """
        return (
            self.use_wallet_provider
            and self.wallet_provider is not None
            and self.wallet_provider != "none"
        )
