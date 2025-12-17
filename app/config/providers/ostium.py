"""Ostium provider configuration."""

from pydantic import Field, field_validator

from app.config.providers.base import BaseProviderConfig
from ostium_python_sdk import NetworkConfig, OstiumSDK


class OstiumConfig(BaseProviderConfig):
    """Ostium provider configuration."""

    private_key: str = Field(default="", description="Private key for signing")
    rpc_url: str = Field(default="", description="RPC URL for blockchain connection")
    network: str = Field(
        default="testnet", description="Network: 'testnet' or 'mainnet'"
    )
    verbose: bool = Field(default=False, description="Enable verbose logging")
    slippage_percentage: float = Field(
        default=1.0, description="Default slippage percentage"
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
        """Create Ostium SDK instance."""
        if not self.private_key:
            raise ValueError("Ostium private_key is required")
        if not self.rpc_url:
            raise ValueError("Ostium rpc_url is required")

        config = self.get_network_config()
        return OstiumSDK(
            config,
            self.private_key,
            self.rpc_url,
            verbose=self.verbose,
        )

