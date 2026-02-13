"""Task management API endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/crawl")
async def trigger_crawl() -> dict[str, str]:
    """Manually trigger a paper crawl task."""
    # TODO: Dispatch Celery task in Phase 2
    return {"status": "not_implemented", "message": "Crawl tasks will be available in Phase 2"}


@router.get("/{task_id}")
async def get_task_status(task_id: str) -> dict[str, str]:
    """Get the status of an async task."""
    # TODO: Query Celery task result in Phase 2
    return {"task_id": task_id, "status": "unknown"}
