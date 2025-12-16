"""Celery application configuration."""

from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "app",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.example_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Optional: Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    # Example: Run every 5 minutes
    # "periodic-task-example": {
    #     "task": "app.tasks.example_tasks.example_periodic_task",
    #     "schedule": 300.0,  # 5 minutes in seconds
    # },
}
