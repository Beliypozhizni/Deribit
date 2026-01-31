from __future__ import annotations

from celery import Celery

from src.config import settings

celery_app = Celery(
    "celery_app",
    broker=settings.celery_broker_url,
    include=["src.worker.tasks"],
)

celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    task_serializer="json",
    accept_content=["json"],
    task_ignore_result=True,
)


celery_app.conf.beat_schedule = {
    "collect-deribit-prices-every-minute": {
        "task": "src.worker.tasks.collect_and_save_prices",
        "schedule": 60.0,
    }
}
