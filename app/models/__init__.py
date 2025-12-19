"""Models module."""

from app.models.analytics import TradeHistory, UserStats
from app.models.auth import OAuthConnection, Session, WalletConnection
from app.models.enums import (
    AuthMethod,
    FeatureAccessLevel,
    OrderSide,
    OrderStatus,
    OrderType,
    PositionSide,
    TradeSide,
    TradeStatus,
    WalletType,
)
from app.models.ostium_settings import OstiumSettings
from app.models.provider import OstiumWallet
from app.models.trading import Order, Position, Trade
from app.models.user import User
from app.models.wallet import Wallet

__all__ = [
    # User
    "User",
    # Authentication
    "OAuthConnection",
    "WalletConnection",
    "Session",
    # Wallet
    "Wallet",
    # Trading
    "Order",
    "Trade",
    "Position",
    # Provider
    "OstiumSettings",
    "OstiumWallet",
    # Analytics
    "TradeHistory",
    "UserStats",
    # Enums
    "AuthMethod",
    "WalletType",
    "FeatureAccessLevel",
    "OrderType",
    "OrderSide",
    "OrderStatus",
    "TradeSide",
    "TradeStatus",
    "PositionSide",
]
