"""Test additional repository methods."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.deposit import Deposit, TokenSwap
from app.models.risk import RiskEvent, RiskLimit
from app.models.trading import Position
from app.repositories.deposit_repository import DepositRepository, TokenSwapRepository
from app.repositories.position_repository import PositionRepository
from app.repositories.risk_repository import RiskEventRepository, RiskLimitRepository


class TestPositionRepository:
    """Test PositionRepository class."""

    @pytest.fixture
    def position_repo(self):
        """Create PositionRepository instance."""
        return PositionRepository()

    @pytest.mark.asyncio
    async def test_get_by_user(self, position_repo, db_session):
        """Test getting positions by user."""
        mock_position = MagicMock(spec=Position)
        mock_position.id = 1
        mock_position.user_id = 1

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_position]
            mock_execute.return_value = mock_result

            positions = await position_repo.get_by_user(db_session, user_id=1)

            assert len(positions) == 1

    @pytest.mark.asyncio
    async def test_get_by_trade_id(self, position_repo, db_session):
        """Test getting position by trade ID."""
        mock_position = MagicMock(spec=Position)
        mock_position.id = 1
        mock_position.trade_id = 123

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_position
            mock_execute.return_value = mock_result

            position = await position_repo.get_by_trade_id(db_session, trade_id=123)

            assert position is not None
            assert position.trade_id == 123


class TestRiskLimitRepository:
    """Test RiskLimitRepository class."""

    @pytest.fixture
    def risk_limit_repo(self):
        """Create RiskLimitRepository instance."""
        return RiskLimitRepository()

    @pytest.mark.asyncio
    async def test_get_by_user_with_asset(self, risk_limit_repo, db_session):
        """Test getting risk limit by user with asset."""
        mock_limit = MagicMock(spec=RiskLimit)
        mock_limit.user_id = 1
        mock_limit.asset = "BTC"

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_limit
            mock_execute.return_value = mock_result

            limit = await risk_limit_repo.get_by_user(db_session, user_id=1, asset="BTC")

            assert limit is not None

    @pytest.mark.asyncio
    async def test_get_by_asset(self, risk_limit_repo, db_session):
        """Test getting global risk limit by asset."""
        mock_limit = MagicMock(spec=RiskLimit)
        mock_limit.asset = "BTC"
        mock_limit.user_id = None

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_limit
            mock_execute.return_value = mock_result

            limit = await risk_limit_repo.get_by_asset(db_session, asset="BTC")

            assert limit is not None

    @pytest.mark.asyncio
    async def test_get_global_default(self, risk_limit_repo, db_session):
        """Test getting global default risk limit."""
        mock_limit = MagicMock(spec=RiskLimit)
        mock_limit.user_id = None
        mock_limit.asset = None

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_limit
            mock_execute.return_value = mock_result

            limit = await risk_limit_repo.get_global_default(db_session)

            assert limit is not None

    @pytest.mark.asyncio
    async def test_get_all_active(self, risk_limit_repo, db_session):
        """Test getting all active risk limits."""
        mock_limit = MagicMock(spec=RiskLimit)
        mock_limit.id = 1

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_limit]
            mock_execute.return_value = mock_result

            limits = await risk_limit_repo.get_all_active(db_session)

            assert len(limits) == 1


class TestRiskEventRepository:
    """Test RiskEventRepository class."""

    @pytest.fixture
    def risk_event_repo(self):
        """Create RiskEventRepository instance."""
        return RiskEventRepository()

    @pytest.mark.asyncio
    async def test_get_by_user(self, risk_event_repo, db_session):
        """Test getting risk events by user."""
        mock_event = MagicMock(spec=RiskEvent)
        mock_event.id = 1
        mock_event.user_id = 1

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_event]
            mock_execute.return_value = mock_result

            events = await risk_event_repo.get_by_user(db_session, user_id=1)

            assert len(events) == 1

    @pytest.mark.asyncio
    async def test_create_event(self, risk_event_repo, db_session):
        """Test creating a risk event."""
        mock_event = MagicMock(spec=RiskEvent)
        mock_event.id = 1
        mock_event.user_id = 1
        mock_event.event_type = "leverage_exceeded"

        with patch.object(risk_event_repo, "create", new_callable=AsyncMock, return_value=mock_event):
            event = await risk_event_repo.create_event(
                db=db_session,
                user_id=1,
                event_type="leverage_exceeded",
                threshold=Decimal("10.0"),
                current_value=Decimal("15.0"),
                severity="warning",
            )

            assert event is not None


class TestDepositRepository:
    """Test DepositRepository class."""

    @pytest.fixture
    def deposit_repo(self):
        """Create DepositRepository instance."""
        return DepositRepository()

    @pytest.mark.asyncio
    async def test_get_by_user(self, deposit_repo, db_session):
        """Test getting deposits by user."""
        mock_deposit = MagicMock(spec=Deposit)
        mock_deposit.id = 1
        mock_deposit.user_id = 1

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_deposit]
            mock_execute.return_value = mock_result

            deposits = await deposit_repo.get_by_user(db_session, user_id=1)

            assert len(deposits) == 1

    @pytest.mark.asyncio
    async def test_get_by_status(self, deposit_repo, db_session):
        """Test getting deposits by status."""
        mock_deposit = MagicMock(spec=Deposit)
        mock_deposit.id = 1
        mock_deposit.status = "completed"

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_deposit]
            mock_execute.return_value = mock_result

            deposits = await deposit_repo.get_by_status(db_session, status="completed")

            assert len(deposits) == 1

    @pytest.mark.asyncio
    async def test_get_by_provider(self, deposit_repo, db_session):
        """Test getting deposits by provider."""
        mock_deposit = MagicMock(spec=Deposit)
        mock_deposit.id = 1
        mock_deposit.provider = "ostium"

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_deposit]
            mock_execute.return_value = mock_result

            deposits = await deposit_repo.get_by_provider(db_session, provider="ostium")

            assert len(deposits) == 1

    @pytest.mark.asyncio
    async def test_get_by_transaction_hash(self, deposit_repo, db_session):
        """Test getting deposit by transaction hash."""
        mock_deposit = MagicMock(spec=Deposit)
        mock_deposit.id = 1
        mock_deposit.transaction_hash = "0xabc123"

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_deposit
            mock_execute.return_value = mock_result

            deposit = await deposit_repo.get_by_transaction_hash(db_session, transaction_hash="0xabc123")

            assert deposit is not None


class TestTokenSwapRepository:
    """Test TokenSwapRepository class."""

    @pytest.fixture
    def swap_repo(self):
        """Create TokenSwapRepository instance."""
        return TokenSwapRepository()

    @pytest.mark.asyncio
    async def test_get_by_deposit(self, swap_repo, db_session):
        """Test getting swaps by deposit ID."""
        mock_swap = MagicMock(spec=TokenSwap)
        mock_swap.id = 1
        mock_swap.deposit_id = 1

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_swap]
            mock_execute.return_value = mock_result

            swaps = await swap_repo.get_by_deposit(db_session, deposit_id=1)

            assert len(swaps) == 1

    @pytest.mark.asyncio
    async def test_get_by_status(self, swap_repo, db_session):
        """Test getting swaps by status."""
        mock_swap = MagicMock(spec=TokenSwap)
        mock_swap.id = 1
        mock_swap.swap_status = "completed"

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = [mock_swap]
            mock_execute.return_value = mock_result

            swaps = await swap_repo.get_by_status(db_session, status="completed")

            assert len(swaps) == 1

    @pytest.mark.asyncio
    async def test_get_by_transaction_hash(self, swap_repo, db_session):
        """Test getting swap by transaction hash."""
        mock_swap = MagicMock(spec=TokenSwap)
        mock_swap.id = 1
        mock_swap.swap_transaction_hash = "0xswap123"

        with patch("sqlalchemy.ext.asyncio.AsyncSession.execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_swap
            mock_execute.return_value = mock_result

            swap = await swap_repo.get_by_transaction_hash(db_session, transaction_hash="0xswap123")

            assert swap is not None

