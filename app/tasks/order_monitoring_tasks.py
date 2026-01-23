"""Order monitoring background tasks."""

import asyncio
import logging
from typing import Any

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="monitor_orders")
def monitor_orders_task() -> dict[str, Any]:
    """Ensure order monitoring service is running for all pending advanced orders.

    This task runs every 1 second to:
    - Check for new pending advanced orders
    - Start monitoring for orders not currently being monitored
    - Clean up monitoring for completed/cancelled orders

    Returns:
        Task result dictionary with monitoring statistics
    """
    from app.core.database import get_session_maker
    from app.models.enums import OrderStatus
    from app.repositories.order_repository import OrderRepository
    from app.services.order_monitoring_service import OrderMonitoringService
    from app.services.price_stream_service import price_stream_service

    async def _monitor() -> dict[str, Any]:
        """Async monitoring logic."""
        AsyncSessionLocal = get_session_maker()
        async with AsyncSessionLocal() as db:
            order_repo = OrderRepository()
            monitoring_service = OrderMonitoringService(db, price_stream_service)

            pending_orders = await order_repo.get_all_by_status(
                db, status=OrderStatus.PENDING, skip=0, limit=1000
            )

            advanced_order_types = ["stop_loss", "take_profit", "trailing_stop", "oco"]
            advanced_orders = [
                order for order in pending_orders if order.order_type.value in advanced_order_types
            ]

            logger.debug(f"Found {len(advanced_orders)} pending advanced orders")

            orders_started = 0
            errors = 0

            for order in advanced_orders:
                try:
                    if order.id not in monitoring_service._monitoring_tasks:
                        await monitoring_service.monitor_order(order.id)
                        orders_started += 1
                        logger.info(
                            f"Started monitoring order {order.id} ({order.order_type.value})"
                        )

                except Exception as e:
                    errors += 1
                    logger.error(
                        f"Error starting monitoring for order {order.id}: {str(e)}",
                        exc_info=True,
                    )

            return {
                "status": "completed",
                "orders_checked": len(advanced_orders),
                "orders_started": orders_started,
                "active_monitors": len(monitoring_service._monitoring_tasks),
                "errors": errors,
            }

    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_monitor())
    except Exception as e:
        logger.error(f"Fatal error in monitor_orders task: {str(e)}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "orders_checked": 0,
            "orders_started": 0,
            "active_monitors": 0,
            "errors": 1,
        }

    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_monitor())
    except Exception as e:
        logger.error(f"Fatal error in monitor_orders task: {str(e)}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "orders_checked": 0,
            "orders_triggered": 0,
            "trailing_stops_updated": 0,
            "errors": 1,
        }
