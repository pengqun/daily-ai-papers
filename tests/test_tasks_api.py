"""Tests for the task management API endpoints.

These tests mock Celery so no broker (Redis) is required.
"""

from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_trigger_crawl_dispatches_task(api_client: AsyncClient) -> None:
    """POST /tasks/crawl should dispatch crawl_all_sources and return a task ID."""
    with patch("daily_ai_papers.api.tasks.crawl_all_sources") as mock_task:
        mock_result = MagicMock()
        mock_result.id = "abc-123"
        mock_task.delay.return_value = mock_result

        resp = await api_client.post("/api/v1/tasks/crawl")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "dispatched"
    assert data["task_id"] == "abc-123"
    mock_task.delay.assert_called_once()


@pytest.mark.asyncio
async def test_get_task_status_pending(api_client: AsyncClient) -> None:
    """GET /tasks/{id} should return PENDING for an unknown task."""
    with patch("daily_ai_papers.api.tasks.AsyncResult") as mock_ar_cls:
        mock_result = MagicMock()
        mock_result.status = "PENDING"
        mock_result.ready.return_value = False
        mock_ar_cls.return_value = mock_result

        resp = await api_client.get("/api/v1/tasks/unknown-id")

    assert resp.status_code == 200
    data = resp.json()
    assert data["task_id"] == "unknown-id"
    assert data["status"] == "PENDING"
    assert "result" not in data
    assert "error" not in data


@pytest.mark.asyncio
async def test_get_task_status_success(api_client: AsyncClient) -> None:
    """GET /tasks/{id} should include result when the task succeeded."""
    with patch("daily_ai_papers.api.tasks.AsyncResult") as mock_ar_cls:
        mock_result = MagicMock()
        mock_result.status = "SUCCESS"
        mock_result.ready.return_value = True
        mock_result.successful.return_value = True
        mock_result.result = {"new_papers": 5}
        mock_ar_cls.return_value = mock_result

        resp = await api_client.get("/api/v1/tasks/done-id")

    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert data["result"] == "{'new_papers': 5}"


@pytest.mark.asyncio
async def test_get_task_status_failure(api_client: AsyncClient) -> None:
    """GET /tasks/{id} should include error when the task failed."""
    with patch("daily_ai_papers.api.tasks.AsyncResult") as mock_ar_cls:
        mock_result = MagicMock()
        mock_result.status = "FAILURE"
        mock_result.ready.return_value = True
        mock_result.successful.return_value = False
        mock_result.result = RuntimeError("broker down")
        mock_ar_cls.return_value = mock_result

        resp = await api_client.get("/api/v1/tasks/fail-id")

    data = resp.json()
    assert data["status"] == "FAILURE"
    assert "broker down" in data["error"]
