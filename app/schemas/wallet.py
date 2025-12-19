"""Wallet schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import WalletType


class WalletCreate(BaseModel):
    """Schema for creating a wallet."""

    provider_type: str  # privy, dynamic
    provider_wallet_id: str
    wallet_address: str
    network: str  # testnet, mainnet
    metadata: dict[str, Any] = Field(default_factory=dict)


class WalletResponse(BaseModel):
    """Schema for wallet response."""

    id: int
    provider_type: str
    wallet_address: str
    network: str
    is_active: bool
    is_primary: bool
    created_at: datetime


class WalletConnectionResponse(BaseModel):
    """Schema for wallet connection response."""

    id: int
    wallet_address: str
    wallet_type: WalletType
    provider: str | None
    is_primary: bool
    verified: bool
    verified_at: datetime | None
    last_used_at: datetime | None
    created_at: datetime
