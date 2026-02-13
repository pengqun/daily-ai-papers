"""Celery application configuration."""

from celery import Celery
from celery.schedules import crontab

from daily_ai_papers.config import settings

app = Celery("daily_ai_papers", broker=settings.redis_url)

app.conf.update(
    result_backend=settings.redis_url,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    beat_schedule={
        "daily-crawl": {
            "task": "daily_ai_papers.tasks.crawl_tasks.crawl_all_sources",
            "schedule": crontab(hour=settings.crawl_schedule_hour, minute=0),
        },
    },
)

app.autodiscover_tasks(["daily_ai_papers.tasks"])
