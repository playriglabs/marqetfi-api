"""Schemas module."""

from app.schemas.analytics import TradeHistoryResponse, UserStatsResponse
from app.schemas.auth import (
    AuthRequest,
    LoginRequest,
    OAuthRequest,
    TokenResponse,
    WalletConnectRequest,
)
from app.schemas.health import HealthResponse
from app.schemas.price import PriceResponse
from app.schemas.trading import (
    OrderCreate,
    OrderResponse,
    PairResponse,
    PositionResponse,
    TradeCreate,
    TradeResponse,
    TradeUpdate,
)
from app.schemas.user import UserCreate, UserResponse
from app.schemas.wallet import WalletConnectionResponse, WalletCreate, WalletResponse

__all__ = [
    # Auth
    "LoginRequest",
    "TokenResponse",
    "AuthRequest",
    "OAuthRequest",
    "WalletConnectRequest",
    # User
    "UserCreate",
    "UserResponse",
    # Trading
    "TradeCreate",
    "TradeResponse",
    "TradeUpdate",
    "OrderCreate",
    "OrderResponse",
    "PositionResponse",
    "PairResponse",
    # Wallet
    "WalletCreate",
    "WalletResponse",
    "WalletConnectionResponse",
    # Analytics
    "TradeHistoryResponse",
    "UserStatsResponse",
    # Health
    "HealthResponse",
    # Price
    "PriceResponse",
]
