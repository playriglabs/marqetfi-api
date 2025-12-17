"""API dependencies."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.services.price_feed_service import PriceFeedService
from app.services.providers.base import (
    BasePriceProvider,
    BaseSettlementProvider,
    BaseTradingProvider,
)
from app.services.providers.factory import ProviderFactory
from app.services.settlement_service import SettlementService
from app.services.trading_service import TradingService

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get current authenticated user."""
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id: int | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # TODO: Fetch user from database
    return {"id": user_id}


async def get_current_active_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Get current active user."""
    # TODO: Check if user is active
    return current_user


async def get_trading_provider() -> BaseTradingProvider:
    """Get configured trading provider."""
    return await ProviderFactory.get_trading_provider()


async def get_price_provider() -> BasePriceProvider:
    """Get configured price provider."""
    return await ProviderFactory.get_price_provider()


async def get_settlement_provider() -> BaseSettlementProvider:
    """Get configured settlement provider."""
    return await ProviderFactory.get_settlement_provider()


async def get_trading_service() -> TradingService:
    """Get trading service instance with multi-provider routing."""
    # Pass None to enable multi-provider routing via ProviderRouter
    return TradingService(trading_provider=None)


async def get_settlement_service() -> SettlementService:
    """Get settlement service instance with multi-provider routing."""
    # Pass None to enable multi-provider routing via ProviderRouter
    return SettlementService(settlement_provider=None)


async def get_price_feed_service() -> PriceFeedService:
    """Get price feed service instance with multi-provider routing."""
    # Pass None to enable multi-provider routing via ProviderRouter
    return PriceFeedService(price_provider=None)
