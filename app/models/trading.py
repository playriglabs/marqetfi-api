"""Trading models."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import OrderSide, OrderStatus, OrderType, PositionSide, TradeSide, TradeStatus

if TYPE_CHECKING:
    from app.models.analytics import TradeHistory
    from app.models.user import User


class Order(Base):
    """Trading order model."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_type: Mapped[OrderType] = mapped_column(String(20), nullable=False)  # market, limit, stop
    side: Mapped[OrderSide] = mapped_column(String(10), nullable=False)  # buy, sell
    asset: Mapped[str] = mapped_column(String(20), nullable=False)  # BTC, ETH, EURUSD, etc.
    quote: Mapped[str] = mapped_column(String(20), nullable=False)  # USDT, USD, etc.
    quantity: Mapped[Decimal] = mapped_column(Numeric(36, 18), nullable=False)
    price: Mapped[Decimal | None] = mapped_column(
        Numeric(36, 18), nullable=True
    )  # For limit orders
    leverage: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[OrderStatus] = mapped_column(String(20), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # ostium, lighter
    provider_order_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    transaction_hash: Mapped[str | None] = mapped_column(String(66), nullable=True)
    filled_quantity: Mapped[Decimal] = mapped_column(
        Numeric(36, 18), default=Decimal("0"), nullable=False
    )
    average_fill_price: Mapped[Decimal | None] = mapped_column(Numeric(36, 18), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    filled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="orders")
    trade: Mapped["Trade | None"] = relationship("Trade", back_populates="order", uselist=False)

    # Indexes
    __table_args__ = (
        Index("ix_orders_user_status", "user_id", "status"),
        Index("ix_orders_provider_order_id", "provider", "provider_order_id"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Order(id={self.id}, asset={self.asset}, status={self.status})>"


class Trade(Base):
    """Trade model."""

    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_id: Mapped[int | None] = mapped_column(
        ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    pair_id: Mapped[int] = mapped_column(Integer, nullable=False)  # Ostium pair ID
    trade_index: Mapped[int] = mapped_column(Integer, nullable=False)  # Ostium trade index
    asset: Mapped[str] = mapped_column(String(20), nullable=False)  # BTC, ETH, EURUSD, etc.
    quote: Mapped[str] = mapped_column(String(20), nullable=False)  # USDT, USD, etc.
    side: Mapped[TradeSide] = mapped_column(String(10), nullable=False)  # long, short
    entry_price: Mapped[Decimal] = mapped_column(Numeric(36, 18), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(36, 18), nullable=False)
    leverage: Mapped[int] = mapped_column(Integer, nullable=False)
    collateral: Mapped[Decimal] = mapped_column(Numeric(36, 18), nullable=False)
    status: Mapped[TradeStatus] = mapped_column(String(20), nullable=False, index=True)
    tp_price: Mapped[Decimal | None] = mapped_column(Numeric(36, 18), nullable=True)
    sl_price: Mapped[Decimal | None] = mapped_column(Numeric(36, 18), nullable=True)
    exit_price: Mapped[Decimal | None] = mapped_column(Numeric(36, 18), nullable=True)
    pnl: Mapped[Decimal | None] = mapped_column(Numeric(36, 18), nullable=True)
    pnl_percentage: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # ostium, lighter
    provider_trade_id: Mapped[str] = mapped_column(String(255), nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="trades")
    order: Mapped["Order | None"] = relationship("Order", back_populates="trade")
    position: Mapped["Position | None"] = relationship(
        "Position", back_populates="trade", uselist=False
    )
    trade_history: Mapped[list["TradeHistory"]] = relationship(
        "TradeHistory", back_populates="trade", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("ix_trades_user_status", "user_id", "status"),
        Index("ix_trades_provider_trade_id", "provider", "provider_trade_id"),
        Index("ix_trades_pair_trade_index", "pair_id", "trade_index"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Trade(id={self.id}, asset={self.asset}, status={self.status})>"


class Position(Base):
    """Position model."""

    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    trade_id: Mapped[int] = mapped_column(
        ForeignKey("trades.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    asset: Mapped[str] = mapped_column(String(20), nullable=False)  # BTC, ETH, EURUSD, etc.
    quote: Mapped[str] = mapped_column(String(20), nullable=False)  # USDT, USD, etc.
    side: Mapped[PositionSide] = mapped_column(String(10), nullable=False)  # long, short
    size: Mapped[Decimal] = mapped_column(Numeric(36, 18), nullable=False)
    entry_price: Mapped[Decimal] = mapped_column(Numeric(36, 18), nullable=False)
    current_price: Mapped[Decimal] = mapped_column(Numeric(36, 18), nullable=False)
    leverage: Mapped[int] = mapped_column(Integer, nullable=False)
    collateral: Mapped[Decimal] = mapped_column(Numeric(36, 18), nullable=False)
    unrealized_pnl: Mapped[Decimal] = mapped_column(Numeric(36, 18), nullable=False)
    unrealized_pnl_percentage: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    liquidation_price: Mapped[Decimal | None] = mapped_column(Numeric(36, 18), nullable=True)
    margin_ratio: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # ostium, lighter
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="positions")
    trade: Mapped["Trade"] = relationship("Trade", back_populates="position")

    # Indexes
    __table_args__ = (Index("ix_positions_user", "user_id"),)

    def __repr__(self) -> str:
        """String representation."""
        return f"<Position(id={self.id}, asset={self.asset}, side={self.side})>"
