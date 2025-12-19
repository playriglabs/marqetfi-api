"""Analytics schemas."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class TradeHistoryResponse(BaseModel):
    """Schema for trade history response."""

    id: int
    trade_id: int
    action: str
    data: dict
    created_at: datetime


class UserStatsResponse(BaseModel):
    """Schema for user stats response."""

    id: int
    user_id: int
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_pnl: Decimal
    total_volume: Decimal
    average_leverage: Decimal
    best_trade_pnl: Decimal | None
    worst_trade_pnl: Decimal | None
    last_trade_at: datetime | None
    calculated_at: datetime
    updated_at: datetime
