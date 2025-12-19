"""Authentication models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import WalletType

if TYPE_CHECKING:
    from app.models.user import User


class OAuthConnection(Base):
    """OAuth provider connection model."""

    __tablename__ = "oauth_connections"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # google, apple
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    access_token: Mapped[str] = mapped_column(Text, nullable=False)  # Encrypted
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)  # Encrypted
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="oauth_connections")

    # Indexes
    __table_args__ = (
        Index("ix_oauth_connections_user_provider", "user_id", "provider"),
        Index("ix_oauth_connections_provider_user_id", "provider", "provider_user_id"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<OAuthConnection(id={self.id}, provider={self.provider})>"


class WalletConnection(Base):
    """External wallet connection model."""

    __tablename__ = "wallet_connections"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    wallet_address: Mapped[str] = mapped_column(String(42), nullable=False, index=True)
    wallet_type: Mapped[WalletType] = mapped_column(
        String(20), nullable=False, default=WalletType.EXTERNAL
    )
    provider: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # privy, dynamic, metamask, walletconnect, coinbase
    provider_wallet_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # Provider-specific wallet ID for MPC wallets
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="wallet_connections")

    # Indexes
    __table_args__ = (Index("ix_wallet_connections_user_primary", "user_id", "is_primary"),)

    def __repr__(self) -> str:
        """String representation."""
        return f"<WalletConnection(id={self.id}, wallet_address={self.wallet_address})>"


class Session(Base):
    """JWT session model."""

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )  # Hashed JWT token
    refresh_token_hash: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    device_info: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)  # IPv6 max length
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")

    # Indexes
    __table_args__ = (Index("ix_sessions_user_expires", "user_id", "expires_at"),)

    def __repr__(self) -> str:
        """String representation."""
        return f"<Session(id={self.id}, user_id={self.user_id})>"
