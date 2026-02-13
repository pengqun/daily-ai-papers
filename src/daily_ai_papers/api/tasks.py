"""Task management API endpoints."""

import logging

from celery.result import AsyncResult
from fastapi import APIRouter

from daily_ai_papers.tasks.celery_app import app as celery_app
from daily_ai_papers.tasks.crawl_tasks import crawl_all_sources

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/crawl")
async def trigger_crawl() -> dict[str, str]:
    """Manually trigger a paper crawl task."""
    result = crawl_all_sources.delay()
    logger.info("Dispatched crawl_all_sources task: %s", result.id)
    return {"status": "dispatched", "task_id": result.id}


@router.get("/{task_id}")
async def get_task_status(task_id: str) -> dict[str, str]:
    """Get the status of an async task."""
    result = AsyncResult(task_id, app=celery_app)
    response: dict[str, str] = {
        "task_id": task_id,
        "status": result.status,
    }
    if result.ready():
        if result.successful():
            response["result"] = str(result.result)
        else:
            response["error"] = str(result.result)
    return response
