"""Wallet models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Wallet(Base):
    """MPC wallet model."""

    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider_type: Mapped[str] = mapped_column(String(50), nullable=False)  # privy, dynamic
    provider_wallet_id: Mapped[str] = mapped_column(String(255), nullable=False)
    wallet_address: Mapped[str] = mapped_column(String(42), nullable=False, index=True)
    network: Mapped[str] = mapped_column(String(20), nullable=False)  # testnet, mainnet
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    wallet_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User", back_populates="wallets", foreign_keys="[Wallet.user_id]"
    )

    # Indexes
    __table_args__ = (
        Index("ix_wallets_user_primary", "user_id", "is_primary"),
        Index("ix_wallets_provider_wallet_id", "provider_type", "provider_wallet_id"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Wallet(id={self.id}, wallet_address={self.wallet_address})>"
