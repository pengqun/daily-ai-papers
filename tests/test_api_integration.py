"""Integration tests for the FastAPI endpoints.

These tests use FastAPI's TestClient. The /submit endpoint hits the real arXiv
API, so these are true integration tests.

Note: Tests that need the database (list_papers, get_paper, submit_paper) are
skipped when PostgreSQL is unavailable.  The health check always runs.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(api_client: AsyncClient) -> None:
    """GET /health should always return ok."""
    resp = await api_client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_openapi_schema_available(api_client: AsyncClient) -> None:
    """The auto-generated OpenAPI schema should be accessible."""
    resp = await api_client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    assert schema["info"]["title"] == "daily-ai-papers"
    # Verify the submit endpoint is documented
    assert "/api/v1/papers/submit" in schema["paths"]
    print(f"\n  OpenAPI paths: {list(schema['paths'].keys())}")


@pytest.mark.asyncio
async def test_submit_paper_validation_error(api_client: AsyncClient) -> None:
    """POST /submit with empty paper_ids should return 422."""
    resp = await api_client.post(
        "/api/v1/papers/submit",
        json={"source": "arxiv", "paper_ids": []},
    )
    assert resp.status_code == 422  # validation error — min_length=1


@pytest.mark.asyncio
async def test_submit_paper_invalid_source(api_client: AsyncClient) -> None:
    """POST /submit with unsupported source should return 422."""
    resp = await api_client.post(
        "/api/v1/papers/submit",
        json={"source": "not_a_real_source", "paper_ids": ["1234.5678"]},
    )
    assert resp.status_code == 422
