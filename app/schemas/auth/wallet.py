"""Wallet authentication schemas."""

from pydantic import BaseModel

from app.models.enums import WalletType


class WalletNonceRequest(BaseModel):
    """Wallet nonce request schema."""

    wallet_address: str


class WalletNonceResponse(BaseModel):
    """Wallet nonce response schema."""

    nonce: str
    message: str


class WalletConnectRequest(BaseModel):
    """Wallet connection request schema."""

    wallet_address: str
    signature: str
    nonce: str
    provider: str | None = None  # metamask, walletconnect, coinbase


class WalletConnectResponse(BaseModel):
    """Wallet connection response schema."""

    id: int
    wallet_address: str
    wallet_type: WalletType
    provider: str | None
    is_primary: bool
    verified: bool
    verified_at: str | None

    class Config:
        """Pydantic config."""

        from_attributes = True


class CreateMPCWalletRequest(BaseModel):
    """Create MPC wallet request schema."""

    provider: str = "privy"  # privy, dynamic


class CreateMPCWalletResponse(BaseModel):
    """Create MPC wallet response schema."""

    wallet_id: int
    wallet_address: str
    provider: str
    provider_wallet_id: str


class WalletConnectionResponse(BaseModel):
    """Wallet connection info schema."""

    id: int
    wallet_address: str
    wallet_type: WalletType
    provider: str | None
    provider_wallet_id: str | None
    is_primary: bool
    verified: bool
    verified_at: str | None
    last_used_at: str | None
    created_at: str

    class Config:
        """Pydantic config."""

        from_attributes = True
