"""Deposit models."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Deposit(Base):
    """Deposit model for tracking user deposits."""

    __tablename__ = "deposits"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_address: Mapped[str] = mapped_column(String(42), nullable=False)  # Token contract address
    token_symbol: Mapped[str] = mapped_column(String(20), nullable=False)  # USDC, USDT, etc.
    chain: Mapped[str] = mapped_column(String(50), nullable=False)  # arbitrum, ethereum, etc.
    amount: Mapped[Decimal] = mapped_column(Numeric(36, 18), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # pending, processing, completed, failed
    provider: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # ostium, lighter - which provider needs this deposit
    transaction_hash: Mapped[str | None] = mapped_column(String(66), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="deposits")
    swaps: Mapped[list["TokenSwap"]] = relationship(
        "TokenSwap", back_populates="deposit", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("ix_deposits_user_status", "user_id", "status"),
        Index("ix_deposits_provider", "provider"),
        Index("ix_deposits_transaction_hash", "transaction_hash"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Deposit(id={self.id}, token={self.token_symbol}, amount={self.amount})>"


class TokenSwap(Base):
    """Token swap model for tracking swap transactions."""

    __tablename__ = "token_swaps"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    deposit_id: Mapped[int] = mapped_column(
        ForeignKey("deposits.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_token: Mapped[str] = mapped_column(String(42), nullable=False)  # Source token address
    to_token: Mapped[str] = mapped_column(String(42), nullable=False)  # Destination token address
    from_chain: Mapped[str] = mapped_column(String(50), nullable=False)  # Source chain
    to_chain: Mapped[str] = mapped_column(String(50), nullable=False)  # Destination chain
    amount: Mapped[Decimal] = mapped_column(Numeric(36, 18), nullable=False)  # Amount being swapped
    swap_provider: Mapped[str] = mapped_column(String(50), nullable=False)  # lifi, symbiosis
    swap_status: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # pending, processing, completed, failed
    swap_transaction_hash: Mapped[str | None] = mapped_column(String(66), nullable=True)
    estimated_output: Mapped[Decimal | None] = mapped_column(Numeric(36, 18), nullable=True)
    actual_output: Mapped[Decimal | None] = mapped_column(Numeric(36, 18), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    deposit: Mapped["Deposit"] = relationship("Deposit", back_populates="swaps")

    # Indexes
    __table_args__ = (
        Index("ix_token_swaps_deposit", "deposit_id"),
        Index("ix_token_swaps_status", "swap_status"),
        Index("ix_token_swaps_transaction_hash", "swap_transaction_hash"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<TokenSwap(id={self.id}, status={self.swap_status})>"
