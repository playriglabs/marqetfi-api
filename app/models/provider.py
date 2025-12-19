"""Provider configuration models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

if TYPE_CHECKING:
    pass


class OstiumWallet(Base):
    """Ostium provider wallet model."""

    __tablename__ = "ostium_wallets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    provider_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, comment="Wallet provider type (privy/dynamic)"
    )
    provider_wallet_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True, comment="Provider-specific wallet ID"
    )
    wallet_address: Mapped[str] = mapped_column(
        String(42), nullable=False, index=True, comment="Ethereum wallet address"
    )
    network: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True, comment="Network (testnet/mainnet)"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="Active status"
    )
    wallet_metadata: Mapped[dict] = mapped_column(
        JSON, nullable=True, default=dict, comment="Provider-specific metadata"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, comment="Creation timestamp"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Last update timestamp",
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<OstiumWallet(id={self.id}, provider={self.provider_type}, "
            f"address={self.wallet_address[:10]}..., network={self.network})>"
        )
