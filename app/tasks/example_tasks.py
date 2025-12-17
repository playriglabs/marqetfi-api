"""Example background tasks."""

from typing import Any

from celery import Task
from loguru import logger

from app.tasks.celery_app import celery_app


class CallbackTask(Task):
    """Base task with callbacks."""

    def on_success(
        self,
        retval: Any,
        task_id: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> None:
        """Success callback."""
        logger.info(f"Task {task_id} succeeded with result: {retval}")

    def on_failure(
        self,
        exc: Exception,
        task_id: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        einfo: Any,
    ) -> None:
        """Failure callback."""
        logger.error(f"Task {task_id} failed with exception: {exc}")


@celery_app.task(base=CallbackTask, bind=True, max_retries=3)
def example_task(self: Any, data: dict) -> dict:
    """Example background task.

    Args:
        data: Task input data

    Returns:
        Task result
    """
    try:
        logger.info(f"Processing task with data: {data}")
        # Your task logic here
        result = {"status": "success", "data": data}
        return result
    except Exception as exc:
        logger.exception(f"Task failed: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2**self.request.retries) from exc


@celery_app.task
def example_periodic_task() -> dict:
    """Example periodic task for Celery Beat."""
    logger.info("Running periodic task")
    # Your periodic task logic here
    return {"status": "completed"}
