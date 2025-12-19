"""Trading schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import OrderSide, OrderType


class TradeCreate(BaseModel):
    """Schema for creating a trade."""

    collateral: float = Field(..., gt=0, description="USDC amount")
    leverage: int = Field(..., ge=1, description="Leverage multiplier")
    asset_type: int = Field(..., description="Asset type (0 for BTC, 1 for ETH, etc.)")
    direction: bool = Field(..., description="True for Long, False for Short")
    order_type: str = Field(..., description="Order type: MARKET, LIMIT, or STOP")
    at_price: float | None = Field(None, gt=0, description="Price for LIMIT or STOP orders")
    tp: float | None = Field(None, gt=0, description="Take Profit price")
    sl: float | None = Field(None, gt=0, description="Stop Loss price")
    asset: str | None = Field(
        None, description="Asset symbol (e.g., BTC, ETH, EURUSD) for provider routing"
    )


class OrderCreate(BaseModel):
    """Schema for creating an order."""

    order_type: OrderType
    side: OrderSide
    asset: str
    quote: str
    quantity: Decimal
    price: Decimal | None = None
    leverage: int = Field(..., ge=1)
    tp: Decimal | None = None
    sl: Decimal | None = None


class TradeResponse(BaseModel):
    """Schema for trade response."""

    id: int | None = Field(default=None, description="Trade ID")
    asset: str | None = Field(default=None, description="Asset symbol")
    quote: str | None = Field(default=None, description="Quote currency")
    side: str | None = Field(default=None, description="Trade side (long/short)")
    entry_price: Decimal | None = Field(default=None, description="Entry price")
    quantity: Decimal | None = Field(default=None, description="Trade quantity")
    leverage: int | None = Field(default=None, description="Leverage multiplier")
    status: str = Field(default="", description="Trade status")
    pnl: Decimal | None = Field(default=None, description="Profit and loss")
    opened_at: datetime | None = Field(default=None, description="Trade open timestamp")
    transaction_hash: str | None = Field(default=None, description="Transaction hash")
    pair_id: int | None = Field(default=None, description="Pair ID")
    trade_index: int | None = Field(default=None, description="Trade index")


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
