"""User model."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AuthMethod, FeatureAccessLevel, WalletType

if TYPE_CHECKING:
    from app.models.analytics import TradeHistory, UserStats
    from app.models.auth import OAuthConnection, Session, WalletConnection
    from app.models.trading import Order, Position, Trade
    from app.models.wallet import Wallet


class User(Base):
    """User model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    auth0_user_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, index=True, nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Authentication fields
    auth_method: Mapped[AuthMethod] = mapped_column(
        SQLEnum(AuthMethod), default=AuthMethod.EMAIL, nullable=False
    )
    wallet_type: Mapped[WalletType | None] = mapped_column(SQLEnum(WalletType), nullable=True)
    wallet_address: Mapped[str | None] = mapped_column(String(42), nullable=True, index=True)
    mpc_wallet_id: Mapped[int | None] = mapped_column(ForeignKey("wallets.id"), nullable=True)
    feature_access_level: Mapped[FeatureAccessLevel] = mapped_column(
        SQLEnum(FeatureAccessLevel), default=FeatureAccessLevel.FULL, nullable=False
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    oauth_connections: Mapped[list["OAuthConnection"]] = relationship(
        "OAuthConnection", back_populates="user", cascade="all, delete-orphan"
    )
    wallet_connections: Mapped[list["WalletConnection"]] = relationship(
        "WalletConnection", back_populates="user", cascade="all, delete-orphan"
    )
    wallets: Mapped[list["Wallet"]] = relationship(
        "Wallet", back_populates="user", cascade="all, delete-orphan"
    )
    orders: Mapped[list["Order"]] = relationship(
        "Order", back_populates="user", cascade="all, delete-orphan"
    )
    trades: Mapped[list["Trade"]] = relationship(
        "Trade", back_populates="user", cascade="all, delete-orphan"
    )
    positions: Mapped[list["Position"]] = relationship(
        "Position", back_populates="user", cascade="all, delete-orphan"
    )
    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )
    trade_history: Mapped[list["TradeHistory"]] = relationship(
        "TradeHistory", back_populates="user", cascade="all, delete-orphan"
    )
    user_stats: Mapped[list["UserStats"]] = relationship(
        "UserStats", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<User(id={self.id}, username={self.username})>"
