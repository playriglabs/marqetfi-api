"""Webhook models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class WebhookConfiguration(Base):
    """Webhook configuration model for event subscriptions."""

    __tablename__ = "webhook_configurations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    secret: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # For HMAC signature verification
    event_types: Mapped[list[str]] = mapped_column(
        JSON, nullable=False
    )  # ["trade.executed", "position.updated", etc.] - stored as JSON for SQLite compatibility
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_delivery_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="webhook_configurations")
    deliveries: Mapped[list["WebhookDelivery"]] = relationship(
        "WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (Index("ix_webhook_configs_user_active", "user_id", "is_active"),)

    def __repr__(self) -> str:
        """String representation."""
        return f"<WebhookConfiguration(id={self.id}, url={self.url}, active={self.is_active})>"


class WebhookDelivery(Base):
    """Webhook delivery log model for tracking delivery attempts."""

    __tablename__ = "webhook_deliveries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    webhook_id: Mapped[int] = mapped_column(
        ForeignKey("webhook_configurations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    delivery_id: Mapped[str] = mapped_column(
        String(36), unique=True, index=True, nullable=False
    )  # UUID for tracking
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)  # JSON payload
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    webhook: Mapped["WebhookConfiguration"] = relationship(
        "WebhookConfiguration", back_populates="deliveries"
    )

    # Indexes
    __table_args__ = (
        Index("ix_webhook_deliveries_webhook_event", "webhook_id", "event_type"),
        Index("ix_webhook_deliveries_retry", "success", "next_retry_at"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<WebhookDelivery(id={self.id}, delivery_id={self.delivery_id}, success={self.success})>"
