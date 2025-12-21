"""Authentication schemas."""

from pydantic import BaseModel, EmailStr

from app.models.enums import AuthMethod
from app.schemas.auth.oauth import OAuthAuthorizeResponse, OAuthConnectionResponse, OAuthLinkRequest
from app.schemas.auth.wallet import (
    CreateMPCWalletRequest,
    CreateMPCWalletResponse,
    WalletConnectionResponse,
    WalletNonceRequest,
    WalletNonceResponse,
)


class RegisterRequest(BaseModel):
    """Registration request schema."""

    email: EmailStr
    password: str
    username: str | None = None


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str


class AuthRequest(BaseModel):
    """Authentication request schema."""

    email: EmailStr | None = None
    password: str | None = None
    wallet_address: str | None = None
    signature: str | None = None
    message: str | None = None
    auth_method: AuthMethod


class OAuthRequest(BaseModel):
    """OAuth request schema."""

    provider: str  # google, apple
    code: str
    state: str


class WalletConnectRequest(BaseModel):
    """Wallet connection request schema."""

    wallet_address: str
    signature: str
    message: str
    provider: str | None = None  # metamask, walletconnect
    create_mpc: bool = False  # True to create MPC wallet


class PrivyVerifyRequest(BaseModel):
    """Privy authentication verification request schema."""

    access_token: str


__all__ = [
    "AuthRequest",
    "LoginRequest",
    "OAuthRequest",
    "RegisterRequest",
    "RefreshTokenRequest",
    "TokenResponse",
    "WalletConnectRequest",
    "PrivyVerifyRequest",
    "OAuthAuthorizeResponse",
    "OAuthConnectionResponse",
    "OAuthLinkRequest",
    "CreateMPCWalletRequest",
    "CreateMPCWalletResponse",
    "WalletConnectionResponse",
    "WalletNonceRequest",
    "WalletNonceResponse",
]
