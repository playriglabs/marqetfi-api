"""Trading schemas."""

from typing import Any

from pydantic import BaseModel, Field


class TradeCreate(BaseModel):
    """Schema for creating a trade."""

    collateral: float = Field(..., gt=0, description="USDC amount")
    leverage: int = Field(..., ge=1, description="Leverage multiplier")
    asset_type: int = Field(..., description="Asset type (0 for BTC, 1 for ETH, etc.)")
    direction: bool = Field(..., description="True for Long, False for Short")
    order_type: str = Field(
        ..., description="Order type: MARKET, LIMIT, or STOP"
    )
    at_price: float | None = Field(
        None, gt=0, description="Price for LIMIT or STOP orders"
    )
    tp: float | None = Field(None, gt=0, description="Take Profit price")
    sl: float | None = Field(None, gt=0, description="Stop Loss price")


class TradeResponse(BaseModel):
    """Schema for trade response."""

    transaction_hash: str = Field(..., description="Transaction hash")
    pair_id: int | None = Field(None, description="Pair ID")
    trade_index: int | None = Field(None, description="Trade index")
    status: str = Field(..., description="Trade status")


class TradeUpdate(BaseModel):
    """Schema for updating trade TP/SL."""

    tp: float | None = Field(None, gt=0, description="Take Profit price")
    sl: float | None = Field(None, gt=0, description="Stop Loss price")


class OrderResponse(BaseModel):
    """Schema for order response."""

    order: dict[str, Any] = Field(..., description="Order details")


class PositionResponse(BaseModel):
    """Schema for position response."""

    trade: dict[str, Any] = Field(..., description="Trade details")
    metrics: dict[str, Any] | None = Field(None, description="Trade metrics")


class PairResponse(BaseModel):
    """Schema for trading pair response."""

    pairs: list[dict[str, Any]] = Field(..., description="Available trading pairs")

