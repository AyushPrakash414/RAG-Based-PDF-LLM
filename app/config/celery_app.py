from celery import Celery
from app.config.settings import get_settings

settings = get_settings()

redis_url = settings.redis_url or "redis://localhost:6379"

celery_app = Celery(
    "rag_tasks",
    broker=redis_url,
    backend=redis_url,
    include=["app.worker.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)
