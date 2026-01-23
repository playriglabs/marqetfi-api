"""Test OrderMonitoringService."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import OrderSide, OrderStatus, OrderType
from app.services.order_monitoring_service import OrderMonitoringService


class TestOrderMonitoringService:
    """Test OrderMonitoringService class."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock(spec=AsyncSession)
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def mock_price_stream(self):
        """Create mock price stream service."""
        stream = MagicMock()
        stream.subscribe = AsyncMock()
        stream.unsubscribe = AsyncMock()
        return stream

    @pytest.fixture
    def service(self, mock_db, mock_price_stream):
        """Create OrderMonitoringService instance."""
        return OrderMonitoringService(db=mock_db, price_stream=mock_price_stream)

    @pytest.fixture
    def mock_stop_loss_order(self):
        """Create mock stop-loss order."""
        order = MagicMock()
        order.id = 1
        order.user_id = 123
        order.asset = "BTC"
        order.quote = "USD"
        order.order_type = OrderType.STOP_LOSS
        order.side = OrderSide.SELL
        order.quantity = Decimal("1.0")
        order.stop_price = Decimal("50000")
        order.status = OrderStatus.PENDING
        order.is_trailing_active = False
        return order

    @pytest.fixture
    def mock_take_profit_order(self):
        """Create mock take-profit order."""
        order = MagicMock()
        order.id = 2
        order.order_type = OrderType.TAKE_PROFIT
        order.side = OrderSide.SELL
        order.stop_price = Decimal("60000")
        order.status = OrderStatus.PENDING
        return order

    @pytest.fixture
    def mock_trailing_stop_order(self):
        """Create mock trailing stop order."""
        order = MagicMock()
        order.id = 3
        order.order_type = OrderType.TRAILING_STOP
        order.side = OrderSide.SELL
        order.stop_price = Decimal("50000")
        order.trailing_offset = Decimal("1000")
        order.status = OrderStatus.PENDING
        order.is_trailing_active = False
        return order

    @pytest.mark.asyncio
    async def test_check_stop_loss_trigger_sell(self, service, mock_stop_loss_order):
        """Test stop-loss triggers for sell order."""
        result = await service._check_stop_loss(mock_stop_loss_order, Decimal("49000"))

        assert result is True

    @pytest.mark.asyncio
    async def test_check_stop_loss_no_trigger_sell(self, service, mock_stop_loss_order):
        """Test stop-loss does not trigger for sell order."""
        result = await service._check_stop_loss(mock_stop_loss_order, Decimal("51000"))

        assert result is False

    @pytest.mark.asyncio
    async def test_check_stop_loss_trigger_buy(self, service, mock_stop_loss_order):
        """Test stop-loss triggers for buy order."""
        mock_stop_loss_order.side = OrderSide.BUY
        mock_stop_loss_order.stop_price = Decimal("50000")

        result = await service._check_stop_loss(mock_stop_loss_order, Decimal("51000"))

        assert result is True

    @pytest.mark.asyncio
    async def test_check_take_profit_trigger_sell(self, service, mock_take_profit_order):
        """Test take-profit triggers for sell order."""
        result = await service._check_take_profit(mock_take_profit_order, Decimal("61000"))

        assert result is True

    @pytest.mark.asyncio
    async def test_check_take_profit_no_trigger_sell(self, service, mock_take_profit_order):
        """Test take-profit does not trigger for sell order."""
        result = await service._check_take_profit(mock_take_profit_order, Decimal("59000"))

        assert result is False

    @pytest.mark.asyncio
    async def test_check_trailing_stop_updates_stop_price(
        self, service, mock_trailing_stop_order, mock_db
    ):
        """Test trailing stop updates stop price as market moves."""
        initial_stop = Decimal("50000")
        mock_trailing_stop_order.stop_price = initial_stop

        result = await service._check_trailing_stop(mock_trailing_stop_order, Decimal("52000"))

        assert result is False
        assert mock_trailing_stop_order.stop_price == Decimal("51000")
        assert mock_trailing_stop_order.is_trailing_active is True
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_check_trailing_stop_triggers(self, service, mock_trailing_stop_order, mock_db):
        """Test trailing stop triggers when price crosses stop."""
        mock_trailing_stop_order.stop_price = Decimal("50000")
        mock_trailing_stop_order.is_trailing_active = True

        result = await service._check_trailing_stop(mock_trailing_stop_order, Decimal("49000"))

        assert result is True

    @pytest.mark.asyncio
    async def test_execute_order(self, service, mock_stop_loss_order, mock_db):
        """Test order execution."""
        service.stop_monitoring_order = AsyncMock()

        await service._execute_order(mock_stop_loss_order, Decimal("49000"))

        assert mock_stop_loss_order.status == OrderStatus.FILLED
        assert mock_stop_loss_order.average_fill_price == Decimal("49000")
        assert mock_stop_loss_order.filled_quantity == Decimal("1.0")
        assert mock_stop_loss_order.filled_at is not None
        mock_db.commit.assert_called()
        service.stop_monitoring_order.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_cancel_linked_order(self, service, mock_db):
        """Test cancelling linked OCO order."""
        linked_order = MagicMock()
        linked_order.id = 2
        linked_order.status = OrderStatus.PENDING

        service._get_order_with_lock = AsyncMock(return_value=linked_order)
        service.stop_monitoring_order = AsyncMock()

        await service._cancel_linked_order(2)

        assert linked_order.status == OrderStatus.CANCELLED
        assert linked_order.cancelled_at is not None
        mock_db.commit.assert_called()
        service.stop_monitoring_order.assert_called_once_with(2)

    @pytest.mark.asyncio
    async def test_is_price_fresh(self, service):
        """Test price freshness check."""
        from datetime import datetime

        current_timestamp = int(datetime.utcnow().timestamp())

        assert service._is_price_fresh(current_timestamp) is True
        assert service._is_price_fresh(current_timestamp - 3) is True
        assert service._is_price_fresh(current_timestamp - 10) is False

    @pytest.mark.asyncio
    async def test_check_order_trigger_rejects_stale_price(self, service, mock_db):
        """Test order trigger rejects stale prices."""
        service._is_price_fresh = MagicMock(return_value=False)

        await service._check_order_trigger(1, Decimal("50000"), 1234567890)

        mock_db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_order_with_lock_nowait(self, service, mock_db):
        """Test getting order with NOWAIT lock."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        order = await service._get_order_with_lock(1, nowait=True)

        assert order is None
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_oco_triggers_and_cancels_linked(self, service, mock_db):
        """Test OCO order triggers and cancels linked order."""
        oco_order = MagicMock()
        oco_order.id = 1
        oco_order.order_type = OrderType.OCO
        oco_order.side = OrderSide.BUY
        oco_order.stop_price = Decimal("50000")
        oco_order.linked_order_id = 2
        oco_order.status = OrderStatus.PENDING

        service._cancel_linked_order = AsyncMock()

        result = await service._check_oco(oco_order, Decimal("49000"))

        assert result is True
        service._cancel_linked_order.assert_called_once_with(2)

    @pytest.mark.asyncio
    async def test_monitor_order_starts_monitoring(self, service, mock_stop_loss_order):
        """Test monitoring starts for pending order."""
        service._get_order_with_lock = AsyncMock(return_value=mock_stop_loss_order)
        service._start_order_monitor = AsyncMock()

        await service.monitor_order(1)

        service._start_order_monitor.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_monitoring_order(self, service):
        """Test stopping monitoring for specific order."""
        mock_task = MagicMock()
        mock_task.cancel = MagicMock()
        service._monitoring_tasks[1] = mock_task

        await service.stop_monitoring_order(1)

        mock_task.cancel.assert_called_once()
        assert 1 not in service._monitoring_tasks
