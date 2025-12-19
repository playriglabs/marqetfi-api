"""Application configuration models for database-backed settings."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class AppConfiguration(Base):
    """Application-level configuration settings."""

    __tablename__ = "app_configurations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    config_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    config_value: Mapped[str] = mapped_column(Text, nullable=True)
    config_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # string, int, float, bool, json
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # app, security, database, etc.
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_encrypted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    # Audit
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
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
        Index("idx_app_config_key_active", "config_key", "is_active"),
        Index("idx_app_config_category", "category"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<AppConfiguration(key={self.config_key}, category={self.category})>"


class ProviderConfiguration(Base):
    """Provider configuration settings (generic for all providers)."""

    __tablename__ = "provider_configurations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    provider_name: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # ostium, lighter, lifi, symbiosis, privy, dynamic
    provider_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # trading, price, settlement, swap, wallet
    config_data: Mapped[dict] = mapped_column(JSON, nullable=False)  # All config as JSON
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Audit
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
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
        Index("idx_provider_config_active", "provider_name", "provider_type", "is_active"),
        Index("idx_provider_config_version", "provider_name", "provider_type", "version"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<ProviderConfiguration(provider={self.provider_name}, "
            f"type={self.provider_type}, version={self.version})>"
        )
