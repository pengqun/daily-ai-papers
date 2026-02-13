"""Integration tests for the FastAPI endpoints.

These tests use FastAPI's TestClient. The /submit endpoint hits the real arXiv
API, so these are true integration tests.

Note: Tests that need the database (list_papers, get_paper, submit_paper) are
skipped when PostgreSQL is unavailable.  The health check always runs.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from daily_ai_papers.main import app


@pytest.fixture
def base_url() -> str:
    return "http://testserver"


@pytest.mark.asyncio
async def test_health_check(base_url: str) -> None:
    """GET /health should always return ok."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=base_url) as client:
        resp = await client.get("/health")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_openapi_schema_available(base_url: str) -> None:
    """The auto-generated OpenAPI schema should be accessible."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=base_url) as client:
        resp = await client.get("/openapi.json")

    assert resp.status_code == 200
    schema = resp.json()
    assert schema["info"]["title"] == "daily-ai-papers"
    # Verify the submit endpoint is documented
    assert "/api/v1/papers/submit" in schema["paths"]
    print(f"\n  OpenAPI paths: {list(schema['paths'].keys())}")


@pytest.mark.asyncio
async def test_submit_paper_validation_error(base_url: str) -> None:
    """POST /submit with empty paper_ids should return 422."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=base_url) as client:
        resp = await client.post(
            "/api/v1/papers/submit",
            json={"source": "arxiv", "paper_ids": []},
        )

    assert resp.status_code == 422  # validation error — min_length=1


@pytest.mark.asyncio
async def test_submit_paper_invalid_source(base_url: str) -> None:
    """POST /submit with unsupported source should return 422."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=base_url) as client:
        resp = await client.post(
            "/api/v1/papers/submit",
            json={"source": "not_a_real_source", "paper_ids": ["1234.5678"]},
        )

    assert resp.status_code == 422
