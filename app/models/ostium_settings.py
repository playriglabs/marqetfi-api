"""Ostium settings model."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class OstiumSettings(Base):
    """Ostium provider configuration settings."""

    __tablename__ = "ostium_settings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Connection Settings
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    private_key_encrypted: Mapped[str] = mapped_column(String(500), nullable=False)
    rpc_url: Mapped[str] = mapped_column(String(500), nullable=False)
    network: Mapped[str] = mapped_column(String(20), nullable=False)  # testnet/mainnet
    verbose: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Trading Parameters
    slippage_percentage: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    default_fee_percentage: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    min_fee: Mapped[Decimal] = mapped_column(Numeric(36, 18), nullable=False)
    max_fee: Mapped[Decimal] = mapped_column(Numeric(36, 18), nullable=False)

    # Retry & Timeout Settings
    timeout: Mapped[int] = mapped_column(Integer, nullable=False)
    retry_attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    retry_delay: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)

    # Versioning
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Audit
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    creator: Mapped["User"] = relationship("User", foreign_keys=[created_by])

    # Indexes
    __table_args__ = (
        Index("idx_ostium_settings_active", "is_active", "created_at"),
        Index("idx_ostium_settings_version", "version"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<OstiumSettings(id={self.id}, version={self.version}, is_active={self.is_active})>"
