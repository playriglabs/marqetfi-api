"""Deposit schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class DepositCreate(BaseModel):
    """Schema for creating a deposit."""

    token_address: str = Field(..., description="Token contract address")
    token_symbol: str = Field(..., description="Token symbol (USDC, USDT, etc.)")
    chain: str = Field(..., description="Chain identifier (arbitrum, ethereum, etc.)")
    amount: Decimal = Field(..., gt=0, description="Deposit amount")
    provider: str = Field(..., description="Provider name (ostium, lighter)")
    transaction_hash: str | None = Field(None, description="Transaction hash (optional)")


class DepositResponse(BaseModel):
    """Schema for deposit response."""

    id: int
    user_id: int
    token_address: str
    token_symbol: str
    chain: str
    amount: str
    status: str
    provider: str
    transaction_hash: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class SwapStatusResponse(BaseModel):
    """Schema for swap status response."""

    deposit_id: int
    swap_needed: bool
    swaps: list[dict[str, Any]]


class DepositListResponse(BaseModel):
    """Schema for deposit list response."""

    deposits: list[DepositResponse]
    total: int
    skip: int
    limit: int
