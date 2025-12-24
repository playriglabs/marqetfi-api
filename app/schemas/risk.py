"""Risk management schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class RiskLimitCreate(BaseModel):
    """Schema for creating risk limit."""

    user_id: int | None = Field(None, description="User ID (None for global limit)")
    asset: str | None = Field(None, description="Asset symbol (None for all assets)")
    max_leverage: int = Field(..., description="Maximum leverage allowed")
    max_position_size: Decimal = Field(..., description="Maximum position size")
    min_margin: Decimal = Field(..., description="Minimum margin requirement")
    is_active: bool = Field(default=True, description="Whether limit is active")


class RiskLimitUpdate(BaseModel):
    """Schema for updating risk limit."""

    max_leverage: int | None = Field(None, description="Maximum leverage")
    max_position_size: Decimal | None = Field(None, description="Maximum position size")
    min_margin: Decimal | None = Field(None, description="Minimum margin")
    is_active: bool | None = Field(None, description="Whether limit is active")


class RiskLimitResponse(BaseModel):
    """Schema for risk limit response."""

    id: int
    user_id: int | None
    asset: str | None
    max_leverage: int
    max_position_size: Decimal
    min_margin: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class RiskEventResponse(BaseModel):
    """Schema for risk event response."""

    id: int
    user_id: int
    event_type: str
    threshold: Decimal
    current_value: Decimal
    severity: str
    message: str | None
    position_id: int | None
    created_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class UserRiskMetricsResponse(BaseModel):
    """Schema for user risk metrics response."""

    user_id: int
    total_positions: int
    aggregate_leverage: float
    total_position_size: float
    total_collateral: float
    recent_risk_events: list[dict[str, Any]]


class PlatformRiskMetricsResponse(BaseModel):
    """Schema for platform risk metrics response."""

    total_positions: int
    aggregate_leverage: float
    total_position_size: float
    total_collateral: float
    total_notional: float


class RiskLimitListResponse(BaseModel):
    """Schema for risk limit list response."""

    items: list[RiskLimitResponse]
    total: int
    skip: int
    limit: int


class RiskEventListResponse(BaseModel):
    """Schema for risk event list response."""

    items: list[RiskEventResponse]
    total: int
    skip: int
    limit: int
