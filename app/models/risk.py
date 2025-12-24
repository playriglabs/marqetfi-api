"""Risk management models."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class RiskLimit(Base):
    """Risk limit model for user and asset-specific limits."""

    __tablename__ = "risk_limits"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )  # None = global limit
    asset: Mapped[str | None] = mapped_column(
        String(20), nullable=True, index=True
    )  # None = all assets
    max_leverage: Mapped[int] = mapped_column(Integer, nullable=False)
    max_position_size: Mapped[Decimal] = mapped_column(Numeric(36, 18), nullable=False)
    min_margin: Mapped[Decimal] = mapped_column(Numeric(36, 18), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    user: Mapped["User | None"] = relationship("User", back_populates="risk_limits")

    # Indexes
    __table_args__ = (Index("ix_risk_limits_user_asset", "user_id", "asset"),)

    def __repr__(self) -> str:
        """String representation."""
        return f"<RiskLimit(id={self.id}, user_id={self.user_id}, asset={self.asset})>"


class RiskEvent(Base):
    """Risk event model for tracking risk threshold breaches."""

    __tablename__ = "risk_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # leverage_exceeded, margin_call, liquidation_risk, etc.
    threshold: Mapped[Decimal] = mapped_column(Numeric(36, 18), nullable=False)
    current_value: Mapped[Decimal] = mapped_column(Numeric(36, 18), nullable=False)
    severity: Mapped[str] = mapped_column(
        String(20), default="warning", nullable=False
    )  # warning, critical, alert
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    position_id: Mapped[int | None] = mapped_column(
        ForeignKey("positions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="risk_events")

    # Indexes
    __table_args__ = (Index("ix_risk_events_user_created", "user_id", "created_at"),)

    def __repr__(self) -> str:
        """String representation."""
        return f"<RiskEvent(id={self.id}, user_id={self.user_id}, event_type={self.event_type})>"
