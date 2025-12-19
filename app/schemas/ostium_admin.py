"""Ostium admin API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class OstiumSettingsCreate(BaseModel):
    """Schema for creating Ostium settings."""

    enabled: bool = Field(default=True, description="Enable/disable provider")
    private_key: str = Field(default="", description="Private key for signing (will be encrypted)")
    rpc_url: str = Field(..., description="RPC URL for blockchain connection")
    network: str = Field(default="testnet", description="Network: 'testnet' or 'mainnet'")
    verbose: bool = Field(default=False, description="Enable verbose logging")
    slippage_percentage: float = Field(
        default=1.0, ge=0.0, le=100.0, description="Default slippage percentage (0-100)"
    )
    default_fee_percentage: float = Field(
        default=0.1, ge=0.0, le=100.0, description="Default fee percentage (0-100)"
    )
    min_fee: float = Field(default=0.01, ge=0.0, description="Minimum fee amount")
    max_fee: float = Field(default=10.0, ge=0.0, description="Maximum fee amount")
    timeout: int = Field(default=30, gt=0, le=300, description="Request timeout in seconds")
    retry_attempts: int = Field(default=3, ge=0, le=10, description="Number of retry attempts")
    retry_delay: float = Field(default=1.0, ge=0.0, description="Delay between retries in seconds")
    activate: bool = Field(default=False, description="Activate these settings immediately")

    @field_validator("network")
    @classmethod
    def validate_network(cls, v: str) -> str:
        """Validate network value."""
        if v.lower() not in ["testnet", "mainnet"]:
            raise ValueError("network must be 'testnet' or 'mainnet'")
        return v.lower()

    @field_validator("max_fee")
    @classmethod
    def validate_max_fee(cls, v: float, info: object) -> float:
        """Validate max_fee is greater than min_fee."""
        if hasattr(info, "data") and "min_fee" in info.data and v <= info.data["min_fee"]:
            raise ValueError("max_fee must be greater than min_fee")
        return v


class OstiumSettingsUpdate(BaseModel):
    """Schema for updating Ostium settings."""

    enabled: bool | None = Field(None, description="Enable/disable provider")
    private_key: str | None = Field(None, description="Private key for signing (will be encrypted)")
    rpc_url: str | None = Field(None, description="RPC URL for blockchain connection")
    network: str | None = Field(None, description="Network: 'testnet' or 'mainnet'")
    verbose: bool | None = Field(None, description="Enable verbose logging")
    slippage_percentage: float | None = Field(
        None, ge=0.0, le=100.0, description="Default slippage percentage (0-100)"
    )
    default_fee_percentage: float | None = Field(
        None, ge=0.0, le=100.0, description="Default fee percentage (0-100)"
    )
    min_fee: float | None = Field(None, ge=0.0, description="Minimum fee amount")
    max_fee: float | None = Field(None, ge=0.0, description="Maximum fee amount")
    timeout: int | None = Field(None, gt=0, le=300, description="Request timeout in seconds")
    retry_attempts: int | None = Field(None, ge=0, le=10, description="Number of retry attempts")
    retry_delay: float | None = Field(None, ge=0.0, description="Delay between retries in seconds")

    @field_validator("network")
    @classmethod
    def validate_network(cls, v: str | None) -> str | None:
        """Validate network value."""
        if v is not None and v.lower() not in ["testnet", "mainnet"]:
            raise ValueError("network must be 'testnet' or 'mainnet'")
        return v.lower() if v else None


class OstiumSettingsResponse(BaseModel):
    """Schema for Ostium settings response."""

    id: int
    enabled: bool
    rpc_url: str
    network: str
    verbose: bool
    slippage_percentage: float
    default_fee_percentage: float
    min_fee: float
    max_fee: float
    timeout: int
    retry_attempts: int
    retry_delay: float
    is_active: bool
    version: int
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class OstiumSettingsHistoryResponse(BaseModel):
    """Schema for paginated settings history response."""

    items: list[OstiumSettingsResponse]
    total: int
    skip: int
    limit: int
