"""Order monitoring service for advanced order execution."""

# mypy: disable-error-code="attr-defined"

import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.enums import OrderStatus, OrderType
from app.models.trading import Order
from app.services.price_stream_service import PriceStreamService


class OrderMonitoringService:
    """Service for monitoring and executing advanced order types."""

    MAX_PRICE_AGE_SECONDS = 5
    PRICE_CHECK_INTERVAL = 1.0

    def __init__(
        self,
        db: AsyncSession,
        price_stream: PriceStreamService,
    ):
        """Initialize order monitoring service.

        Args:
            db: Database session
            price_stream: Price stream service for real-time prices
        """
        self.db = db
        self.price_stream = price_stream
        self._monitoring_tasks: dict[int, asyncio.Task[None]] = {}
        self._running = False

    async def start_monitoring(self) -> None:
        """Start monitoring all active advanced orders."""
        if self._running:
            logger.warning("Order monitoring already running")
            return

        self._running = True
        logger.info("Order monitoring started")

        active_orders = await self._get_active_advanced_orders()

        for order in active_orders:
            await self._start_order_monitor(order)

    async def stop_monitoring(self) -> None:
        """Stop all order monitoring tasks."""
        self._running = False

        for task in self._monitoring_tasks.values():
            task.cancel()

        await asyncio.gather(*self._monitoring_tasks.values(), return_exceptions=True)
        self._monitoring_tasks.clear()

        logger.info("Order monitoring stopped")

    async def monitor_order(self, order_id: int) -> None:
        """Start monitoring a specific order.

        Args:
            order_id: Order ID to monitor
        """
        order = await self._get_order_with_lock(order_id)
        if order and order.status == OrderStatus.PENDING:
            await self._start_order_monitor(order)

    async def stop_monitoring_order(self, order_id: int) -> None:
        """Stop monitoring a specific order.

        Args:
            order_id: Order ID to stop monitoring
        """
        if order_id in self._monitoring_tasks:
            self._monitoring_tasks[order_id].cancel()
            try:
                await self._monitoring_tasks[order_id]
            except asyncio.CancelledError:
                pass
            del self._monitoring_tasks[order_id]
            logger.info(f"Stopped monitoring order {order_id}")

    async def _start_order_monitor(self, order: Order) -> None:
        """Start monitoring task for an order.

        Args:
            order: Order to monitor
        """
        if order.id in self._monitoring_tasks:
            return

        pair = f"{order.asset}{order.quote}"

        async def price_callback(price: float, timestamp: int, source: str) -> None:
            await self._check_order_trigger(order.id, Decimal(str(price)), timestamp)

        await self.price_stream.subscribe(pair, price_callback)

        task = asyncio.create_task(self._monitor_loop(order.id, pair, price_callback))
        self._monitoring_tasks[order.id] = task

        logger.info(f"Started monitoring order {order.id} ({order.order_type})")

    async def _monitor_loop(
        self,
        order_id: int,
        pair: str,
        callback: Any,
    ) -> None:
        """Monitor loop for order cleanup.

        Args:
            order_id: Order ID
            pair: Trading pair
            callback: Price callback to unsubscribe
        """
        try:
            while self._running:
                await asyncio.sleep(self.PRICE_CHECK_INTERVAL)

                order = await self._get_order_with_lock(order_id)
                if not order or order.status != OrderStatus.PENDING:
                    break

        except asyncio.CancelledError:
            pass
        finally:
            await self.price_stream.unsubscribe(pair, callback)
            if order_id in self._monitoring_tasks:
                del self._monitoring_tasks[order_id]

    async def _check_order_trigger(
        self,
        order_id: int,
        price: Decimal,
        timestamp: int,
    ) -> None:
        """Check if order should be triggered.

        Args:
            order_id: Order ID
            price: Current price
            timestamp: Price timestamp
        """
        if not self._is_price_fresh(timestamp):
            logger.warning(f"Rejecting stale price for order {order_id}")
            return

        order = await self._get_order_with_lock(order_id, nowait=True)

        if not order or order.status != OrderStatus.PENDING:
            return

        triggered = False

        if order.order_type == OrderType.STOP_LOSS:
            triggered = await self._check_stop_loss(order, price)
        elif order.order_type == OrderType.TAKE_PROFIT:
            triggered = await self._check_take_profit(order, price)
        elif order.order_type == OrderType.TRAILING_STOP:
            triggered = await self._check_trailing_stop(order, price)
        elif order.order_type == OrderType.OCO:
            triggered = await self._check_oco(order, price)

        if triggered:
            await self._execute_order(order, price)

    async def _check_stop_loss(self, order: Order, price: Decimal) -> bool:
        """Check stop-loss trigger condition.

        Args:
            order: Order to check
            price: Current price

        Returns:
            True if should trigger
        """
        if not order.stop_price:
            return False

        if order.side.value == "buy" and price >= order.stop_price:
            logger.info(
                f"Stop-loss triggered for order {order.id}: price {price} >= {order.stop_price}"
            )
            return True
        elif order.side.value == "sell" and price <= order.stop_price:
            logger.info(
                f"Stop-loss triggered for order {order.id}: price {price} <= {order.stop_price}"
            )
            return True

        return False

    async def _check_take_profit(self, order: Order, price: Decimal) -> bool:
        """Check take-profit trigger condition.

        Args:
            order: Order to check
            price: Current price

        Returns:
            True if should trigger
        """
        if not order.stop_price:
            return False

        if order.side.value == "sell" and price >= order.stop_price:
            logger.info(
                f"Take-profit triggered for order {order.id}: price {price} >= {order.stop_price}"
            )
            return True
        elif order.side.value == "buy" and price <= order.stop_price:
            logger.info(
                f"Take-profit triggered for order {order.id}: price {price} <= {order.stop_price}"
            )
            return True

        return False

    async def _check_trailing_stop(self, order: Order, price: Decimal) -> bool:
        """Check and update trailing stop.

        Args:
            order: Order to check
            price: Current price

        Returns:
            True if should trigger
        """
        if not order.trailing_offset or not order.stop_price:
            return False

        if not order.is_trailing_active:
            order.is_trailing_active = True
            await self.db.commit()

        should_update_stop = False

        if order.side.value == "sell":
            new_stop = price - order.trailing_offset
            if new_stop > order.stop_price:
                order.stop_price = new_stop
                should_update_stop = True

            if price <= order.stop_price:
                logger.info(
                    f"Trailing stop triggered for order {order.id}: price {price} <= {order.stop_price}"
                )
                return True

        elif order.side.value == "buy":
            new_stop = price + order.trailing_offset
            if new_stop < order.stop_price:
                order.stop_price = new_stop
                should_update_stop = True

            if price >= order.stop_price:
                logger.info(
                    f"Trailing stop triggered for order {order.id}: price {price} >= {order.stop_price}"
                )
                return True

        if should_update_stop:
            await self.db.commit()
            await self.db.refresh(order)
            logger.debug(f"Updated trailing stop for order {order.id}: new stop {order.stop_price}")

        return False

    async def _check_oco(self, order: Order, price: Decimal) -> bool:
        """Check OCO (One-Cancels-Other) trigger.

        Args:
            order: Order to check
            price: Current price

        Returns:
            True if should trigger
        """
        if not order.stop_price:
            return False

        triggered = False

        if order.side.value == "buy" and price <= order.stop_price:
            triggered = True
        elif order.side.value == "sell" and price >= order.stop_price:
            triggered = True

        if triggered:
            logger.info(f"OCO order triggered for order {order.id}")

            if order.linked_order_id:
                await self._cancel_linked_order(order.linked_order_id)

            return True

        return False

    async def _execute_order(self, order: Order, price: Decimal) -> None:
        """Execute triggered order.

        Args:
            order: Order to execute
            price: Trigger price
        """
        order.status = OrderStatus.FILLED
        order.average_fill_price = price
        order.filled_quantity = order.quantity
        order.filled_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(order)

        logger.info(f"Executed order {order.id} at price {price}")

        await self.stop_monitoring_order(order.id)

    async def _cancel_linked_order(self, order_id: int) -> None:
        """Cancel linked OCO order.

        Args:
            order_id: Linked order ID to cancel
        """
        order = await self._get_order_with_lock(order_id)
        if order and order.status == OrderStatus.PENDING:
            order.status = OrderStatus.CANCELLED
            order.cancelled_at = datetime.utcnow()
            await self.db.commit()
            await self.stop_monitoring_order(order_id)
            logger.info(f"Cancelled linked OCO order {order_id}")

    async def _get_active_advanced_orders(self) -> list[Order]:
        """Get all active advanced orders.

        Returns:
            List of pending advanced orders
        """
        result = await self.db.execute(
            select(Order).where(
                Order.status == OrderStatus.PENDING,
                Order.order_type.in_(
                    [
                        OrderType.STOP_LOSS,
                        OrderType.TAKE_PROFIT,
                        OrderType.TRAILING_STOP,
                        OrderType.OCO,
                    ]
                ),
            )
        )
        return list(result.scalars().all())

    async def _get_order_with_lock(
        self,
        order_id: int,
        nowait: bool = False,
    ) -> Order | None:
        """Get order with database lock.

        Args:
            order_id: Order ID
            nowait: Use NOWAIT clause

        Returns:
            Order or None
        """
        try:
            query = select(Order).where(Order.id == order_id).with_for_update(nowait=nowait)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            if nowait:
                logger.debug(f"Order {order_id} locked, skipping: {e}")
            else:
                logger.error(f"Error getting order {order_id} with lock: {e}")
            return None

    def _is_price_fresh(self, timestamp: int) -> bool:
        """Check if price is fresh enough.

        Args:
            timestamp: Price timestamp (seconds)

        Returns:
            True if price is fresh
        """
        now = int(datetime.utcnow().timestamp())
        age = now - timestamp
        return age <= self.MAX_PRICE_AGE_SECONDS
