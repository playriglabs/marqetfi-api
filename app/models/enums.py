"""Enum definitions for models."""

from enum import Enum


class AuthMethod(str, Enum):
    """Authentication method."""

    EMAIL = "email"
    GOOGLE = "google"
    APPLE = "apple"
    WALLET = "wallet"


class WalletType(str, Enum):
    """Wallet type."""

    MPC = "mpc"
    EXTERNAL = "external"
    NONE = "none"


class FeatureAccessLevel(str, Enum):
    """Feature access level."""

    FULL = "full"
    LIMITED = "limited"


class OrderType(str, Enum):
    """Order type."""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"


class OrderSide(str, Enum):
    """Order side."""

    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    """Order status."""

    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class TradeSide(str, Enum):
    """Trade side."""

    LONG = "long"
    SHORT = "short"


class TradeStatus(str, Enum):
    """Trade status."""

    OPEN = "open"
    CLOSED = "closed"
    LIQUIDATED = "liquidated"


class PositionSide(str, Enum):
    """Position side."""

    LONG = "long"
    SHORT = "short"
