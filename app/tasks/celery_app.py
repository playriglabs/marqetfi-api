"""Celery application configuration."""

from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "app",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.risk_monitoring_tasks",
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
    # Shutdown configuration for graceful termination
    worker_shutdown_timeout=10.0,  # Time to wait for tasks to complete before force shutdown
    worker_disable_rate_limits=False,
    worker_enable_remote_control=True,
    # Graceful shutdown settings
    worker_send_task_events=True,
    task_acks_late=True,  # Acknowledge tasks after completion
    task_reject_on_worker_lost=True,  # Reject tasks if worker dies
)

# Optional: Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    # Risk monitoring: Run every 30 seconds
    "monitor-position-risk": {
        "task": "monitor_position_risk",
        "schedule": 30.0,  # 30 seconds
    },
}
