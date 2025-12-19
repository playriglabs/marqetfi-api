"""Analytics models."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.trading import Trade
    from app.models.user import User


class TradeHistory(Base):
    """Trade history model."""

    __tablename__ = "trade_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    trade_id: Mapped[int] = mapped_column(
        ForeignKey("trades.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # open, close, update_tp, update_sl
    data: Mapped[dict] = mapped_column(JSON, nullable=False)  # Snapshot of trade data
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="trade_history")
    trade: Mapped["Trade"] = relationship("Trade", back_populates="trade_history")

    def __repr__(self) -> str:
        """String representation."""
        return f"<TradeHistory(id={self.id}, action={self.action})>"


class UserStats(Base):
    """User trading statistics model."""

    __tablename__ = "user_stats"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    total_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    winning_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    losing_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_pnl: Mapped[Decimal] = mapped_column(
        Numeric(36, 18), default=Decimal("0"), nullable=False
    )
    total_volume: Mapped[Decimal] = mapped_column(
        Numeric(36, 18), default=Decimal("0"), nullable=False
    )
    average_leverage: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False
    )
    best_trade_pnl: Mapped[Decimal] = mapped_column(Numeric(36, 18), nullable=True)
    worst_trade_pnl: Mapped[Decimal] = mapped_column(Numeric(36, 18), nullable=True)
    last_trade_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="user_stats")

    def __repr__(self) -> str:
        """String representation."""
        return f"<UserStats(id={self.id}, user_id={self.user_id})>"
