"""Tests for paper API endpoints (list, get, submit success path).

Uses mocked database sessions so no PostgreSQL is required.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from daily_ai_papers.models.paper import Paper


def _make_paper(**overrides) -> Paper:  # type: ignore[no-untyped-def]
    """Create a Paper ORM object with test defaults."""
    defaults = dict(
        id=1,
        source="arxiv",
        source_id="2401.00001",
        title="Test Paper",
        abstract="An abstract",
        pdf_url="https://arxiv.org/pdf/2401.00001",
        published_at=datetime(2024, 1, 1, tzinfo=UTC),
        categories=["cs.AI"],
        keywords=["test"],
        status="ready",
        full_text=None,
        summary="A summary",
        summary_zh=None,
        contributions=None,
        methodology=None,
        results=None,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
        updated_at=datetime(2024, 1, 1, tzinfo=UTC),
        authors=[],
    )
    defaults.update(overrides)
    paper = MagicMock(spec=Paper)
    for k, v in defaults.items():
        setattr(paper, k, v)
    return paper


def _mock_db_with_papers(papers: list[Paper]) -> AsyncMock:
    """Create a mocked AsyncSession that returns the given papers from a select."""
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = papers

    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_result.scalar_one.side_effect = lambda: papers[0] if papers else None

    db = AsyncMock()
    db.execute.return_value = mock_result
    return db


class TestListPapers:
    """GET /api/v1/papers endpoint tests."""

    @pytest.mark.asyncio
    async def test_empty_list(self, api_client: AsyncClient) -> None:
        db = _mock_db_with_papers([])

        async def override_get_db():  # type: ignore[no-untyped-def]
            yield db

        with patch("daily_ai_papers.api.papers.get_db", override_get_db):
            from daily_ai_papers.database import get_db
            from daily_ai_papers.main import app

            app.dependency_overrides[get_db] = override_get_db
            try:
                resp = await api_client.get("/api/v1/papers")
            finally:
                app.dependency_overrides.clear()

        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_returns_papers(self, api_client: AsyncClient) -> None:
        papers = [
            _make_paper(id=1, title="Paper A"),
            _make_paper(id=2, title="Paper B"),
        ]
        db = _mock_db_with_papers(papers)

        async def override_get_db():  # type: ignore[no-untyped-def]
            yield db

        from daily_ai_papers.database import get_db
        from daily_ai_papers.main import app

        app.dependency_overrides[get_db] = override_get_db
        try:
            resp = await api_client.get("/api/v1/papers")
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["title"] == "Paper A"
        assert data[1]["title"] == "Paper B"

    @pytest.mark.asyncio
    async def test_pagination_params_accepted(self, api_client: AsyncClient) -> None:
        db = _mock_db_with_papers([])

        async def override_get_db():  # type: ignore[no-untyped-def]
            yield db

        from daily_ai_papers.database import get_db
        from daily_ai_papers.main import app

        app.dependency_overrides[get_db] = override_get_db
        try:
            resp = await api_client.get("/api/v1/papers?page=2&page_size=5")
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_category_filter_accepted(self, api_client: AsyncClient) -> None:
        db = _mock_db_with_papers([])

        async def override_get_db():  # type: ignore[no-untyped-def]
            yield db

        from daily_ai_papers.database import get_db
        from daily_ai_papers.main import app

        app.dependency_overrides[get_db] = override_get_db
        try:
            resp = await api_client.get("/api/v1/papers?category=cs.AI")
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_status_filter_accepted(self, api_client: AsyncClient) -> None:
        db = _mock_db_with_papers([])

        async def override_get_db():  # type: ignore[no-untyped-def]
            yield db

        from daily_ai_papers.database import get_db
        from daily_ai_papers.main import app

        app.dependency_overrides[get_db] = override_get_db
        try:
            resp = await api_client.get("/api/v1/papers?status=ready")
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 200


class TestGetPaper:
    """GET /api/v1/papers/{paper_id} endpoint tests."""

    @pytest.mark.asyncio
    async def test_get_existing_paper(self, api_client: AsyncClient) -> None:
        paper = _make_paper(id=1, title="Found Paper")

        mock_result = MagicMock()
        mock_result.scalar_one.return_value = paper
        db = AsyncMock()
        db.execute.return_value = mock_result

        async def override_get_db():  # type: ignore[no-untyped-def]
            yield db

        from daily_ai_papers.database import get_db
        from daily_ai_papers.main import app

        app.dependency_overrides[get_db] = override_get_db
        try:
            resp = await api_client.get("/api/v1/papers/1")
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Found Paper"
        assert data["id"] == 1

    @pytest.mark.asyncio
    async def test_get_nonexistent_paper_returns_500(self) -> None:
        """When scalar_one() finds no rows, SQLAlchemy raises NoResultFound → 500."""
        from httpx import ASGITransport, AsyncClient as AC
        from sqlalchemy.exc import NoResultFound

        from daily_ai_papers.database import get_db
        from daily_ai_papers.main import app

        mock_result = MagicMock()
        mock_result.scalar_one.side_effect = NoResultFound()
        db = AsyncMock()
        db.execute.return_value = mock_result

        async def override_get_db():  # type: ignore[no-untyped-def]
            yield db

        app.dependency_overrides[get_db] = override_get_db
        try:
            transport = ASGITransport(app=app, raise_app_exceptions=False)
            async with AC(transport=transport, base_url="http://testserver") as client:
                resp = await client.get("/api/v1/papers/999")
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 500


class TestSubmitPaperSuccess:
    """POST /api/v1/papers/submit — successful submission path."""

    @pytest.mark.asyncio
    async def test_successful_submit(self, api_client: AsyncClient) -> None:
        from daily_ai_papers.schemas.paper import SubmitPaperResult

        mock_results = [
            SubmitPaperResult(
                source_id="2401.00001",
                status="queued",
                paper_id=1,
                message="Paper queued for processing",
            ),
        ]

        db = AsyncMock()

        async def override_get_db():  # type: ignore[no-untyped-def]
            yield db

        from daily_ai_papers.database import get_db
        from daily_ai_papers.main import app

        app.dependency_overrides[get_db] = override_get_db
        try:
            with patch(
                "daily_ai_papers.api.papers.submit_papers",
                new_callable=AsyncMock,
                return_value=mock_results,
            ):
                resp = await api_client.post(
                    "/api/v1/papers/submit",
                    json={"source": "arxiv", "paper_ids": ["2401.00001"]},
                )
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["results"][0]["status"] == "queued"
        assert data["results"][0]["source_id"] == "2401.00001"
