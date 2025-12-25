"""Pytest configuration and fixtures."""

# Set test database URL BEFORE any imports that might use it
import os  # noqa: E402

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

import asyncio  # noqa: E402
from collections.abc import AsyncGenerator, Generator  # noqa: E402
from contextlib import asynccontextmanager  # noqa: E402
from typing import Any  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.core.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


# Override lifespan to skip database initialization in tests
@asynccontextmanager
async def test_lifespan(app):
    """Test lifespan that skips database initialization."""
    from app.core.cache import cache_manager

    # Skip database init, just connect cache
    await cache_manager.connect()
    yield
    await cache_manager.disconnect()


# Replace the lifespan
app.router.lifespan_context = test_lifespan

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, Any, None]:
    """Create event loop for tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, Any]:
    """Create database session for tests."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client(db_session: AsyncSession) -> TestClient:
    """Create test client."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# Mock fixtures for providers
@pytest.fixture
def mock_wallet_provider():
    """Create a mock wallet provider."""
    from unittest.mock import AsyncMock, MagicMock

    from app.services.wallet_providers.base import BaseWalletProvider

    mock_provider = MagicMock(spec=BaseWalletProvider)
    mock_provider.create_wallet = AsyncMock(
        return_value={
            "wallet_id": "test_wallet_id",
            "address": "0x1234567890123456789012345678901234567890",
            "network": "testnet",
            "metadata": {},
        }
    )
    mock_provider.get_wallet_address = AsyncMock(
        return_value="0x1234567890123456789012345678901234567890"
    )
    mock_provider.sign_transaction = AsyncMock(return_value="0x" + "a" * 64)
    mock_provider.sign_message = AsyncMock(return_value="0x" + "b" * 64)
    mock_provider.get_wallet_info = AsyncMock(
        return_value={
            "wallet_id": "test_wallet_id",
            "address": "0x1234567890123456789012345678901234567890",
            "network": "testnet",
            "metadata": {},
        }
    )
    mock_provider.initialize = AsyncMock()
    return mock_provider


@pytest.fixture
def mock_trading_provider():
    """Create a mock trading provider."""
    from unittest.mock import AsyncMock, MagicMock

    from app.services.providers.base import BaseTradingProvider

    mock_provider = MagicMock(spec=BaseTradingProvider)
    mock_provider.place_order = AsyncMock()
    mock_provider.cancel_order = AsyncMock()
    mock_provider.get_order_status = AsyncMock()
    mock_provider.get_positions = AsyncMock(return_value=[])
    mock_provider.initialize = AsyncMock()
    return mock_provider


@pytest.fixture
def mock_price_provider():
    """Create a mock price provider."""
    from unittest.mock import AsyncMock, MagicMock

    from app.services.providers.base import BasePriceProvider

    mock_provider = MagicMock(spec=BasePriceProvider)
    mock_provider.get_price = AsyncMock(return_value={"price": 100.0, "timestamp": 1234567890})
    mock_provider.get_orderbook = AsyncMock(return_value={"bids": [], "asks": []})
    mock_provider.initialize = AsyncMock()
    return mock_provider


@pytest.fixture
def mock_auth_provider():
    """Create a mock auth provider."""
    from unittest.mock import AsyncMock, MagicMock

    from app.services.providers.base import BaseAuthProvider

    mock_provider = MagicMock(spec=BaseAuthProvider)
    mock_provider.authenticate = AsyncMock(return_value={"user_id": "123", "email": "test@example.com"})
    mock_provider.get_user_info = AsyncMock(return_value={"user_id": "123", "email": "test@example.com"})
    mock_provider.verify_token = AsyncMock(return_value=True)
    mock_provider.initialize = AsyncMock()
    return mock_provider


# Model fixtures
@pytest.fixture
def sample_ostium_wallet():
    """Create a sample OstiumWallet model instance."""
    from datetime import datetime

    from app.models.provider import OstiumWallet

    return OstiumWallet(
        id=1,
        provider_type="privy",
        provider_wallet_id="test_wallet_id",
        wallet_address="0x1234567890123456789012345678901234567890",
        network="testnet",
        is_active=True,
        metadata={"test": "data"},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
