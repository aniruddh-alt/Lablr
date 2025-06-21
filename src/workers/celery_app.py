from celery import Celery
from ..core.config import get_settings

settings = get_settings()

# Initialize Celery app
celery_app = Celery(
    "lablr_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["src.workers.tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.job_timeout,
    task_soft_time_limit=settings.job_timeout - 60,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
)
