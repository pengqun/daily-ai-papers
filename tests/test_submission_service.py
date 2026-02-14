"""Unit tests for the paper submission service.

Tests _get_crawler, _upsert_paper, and submit_papers using mocked
database sessions and crawlers — no real DB or network required.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from daily_ai_papers.models.paper import Paper
from daily_ai_papers.schemas.paper import SubmitPaperResult
from daily_ai_papers.services.crawler.arxiv import ArxivCrawler
from daily_ai_papers.services.crawler.base import CrawledPaper
from daily_ai_papers.services.submission import _get_crawler, _upsert_paper, submit_papers


def _make_crawled(source_id: str = "2401.00001", title: str = "Test Paper") -> CrawledPaper:
    """Helper to create a CrawledPaper with sensible defaults."""
    return CrawledPaper(
        source="arxiv",
        source_id=source_id,
        title=title,
        abstract="An abstract.",
        pdf_url="https://arxiv.org/pdf/2401.00001",
        published_at=datetime(2024, 1, 1, tzinfo=UTC),
        categories=["cs.AI"],
        author_names=["Alice", "Bob"],
    )


class TestGetCrawler:
    """Test the crawler registry lookup."""

    def test_arxiv_returns_crawler(self) -> None:
        crawler = _get_crawler("arxiv")
        assert isinstance(crawler, ArxivCrawler)

    def test_unknown_source_raises(self) -> None:
        with pytest.raises(ValueError, match="Unsupported paper source"):
            _get_crawler("not_a_source")

    def test_semantic_scholar_not_yet_supported(self) -> None:
        with pytest.raises(ValueError, match="Unsupported paper source"):
            _get_crawler("semantic_scholar")


class TestUpsertPaper:
    """Test the _upsert_paper helper with a mocked AsyncSession."""

    @pytest.mark.asyncio
    async def test_new_paper_is_created(self) -> None:
        crawled = _make_crawled()

        # Mock the DB session: execute returns no existing paper
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        db = AsyncMock()
        db.execute.return_value = mock_result

        paper, is_new = await _upsert_paper(db, crawled)

        assert is_new is True
        assert paper.source == "arxiv"
        assert paper.source_id == "2401.00001"
        assert paper.title == "Test Paper"
        assert paper.status == "crawled"
        db.add.assert_called_once_with(paper)
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_existing_paper_is_returned(self) -> None:
        crawled = _make_crawled()

        existing_paper = Paper(
            id=42,
            source="arxiv",
            source_id="2401.00001",
            title="Existing Paper",
            status="ready",
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_paper

        db = AsyncMock()
        db.execute.return_value = mock_result

        paper, is_new = await _upsert_paper(db, crawled)

        assert is_new is False
        assert paper.id == 42
        assert paper.title == "Existing Paper"
        db.add.assert_not_called()
        db.flush.assert_not_awaited()


class TestSubmitPapers:
    """Test the submit_papers orchestration function."""

    @pytest.mark.asyncio
    async def test_new_paper_returns_queued(self) -> None:
        crawled = _make_crawled()

        mock_crawler = AsyncMock()
        mock_crawler.fetch_paper_by_id.return_value = crawled

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        db = AsyncMock()
        db.execute.return_value = mock_result

        with patch("daily_ai_papers.services.submission._get_crawler", return_value=mock_crawler):
            results = await submit_papers("arxiv", ["2401.00001"], db)

        assert len(results) == 1
        assert results[0].status == "queued"
        assert results[0].source_id == "2401.00001"
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_duplicate_paper_returns_duplicate(self) -> None:
        crawled = _make_crawled()
        existing = Paper(id=10, source="arxiv", source_id="2401.00001", title="X", status="ready")

        mock_crawler = AsyncMock()
        mock_crawler.fetch_paper_by_id.return_value = crawled

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing

        db = AsyncMock()
        db.execute.return_value = mock_result

        with patch("daily_ai_papers.services.submission._get_crawler", return_value=mock_crawler):
            results = await submit_papers("arxiv", ["2401.00001"], db)

        assert len(results) == 1
        assert results[0].status == "duplicate"
        assert results[0].paper_id == 10

    @pytest.mark.asyncio
    async def test_not_found_paper(self) -> None:
        mock_crawler = AsyncMock()
        mock_crawler.fetch_paper_by_id.return_value = None

        db = AsyncMock()

        with patch("daily_ai_papers.services.submission._get_crawler", return_value=mock_crawler):
            results = await submit_papers("arxiv", ["9999.99999"], db)

        assert len(results) == 1
        assert results[0].status == "not_found"
        assert "9999.99999" in results[0].message

    @pytest.mark.asyncio
    async def test_crawler_exception_returns_error(self) -> None:
        mock_crawler = AsyncMock()
        mock_crawler.fetch_paper_by_id.side_effect = RuntimeError("network error")

        db = AsyncMock()

        with patch("daily_ai_papers.services.submission._get_crawler", return_value=mock_crawler):
            results = await submit_papers("arxiv", ["2401.00001"], db)

        assert len(results) == 1
        assert results[0].status == "error"
        assert "Failed" in results[0].message

    @pytest.mark.asyncio
    async def test_mixed_results(self) -> None:
        """Submit multiple papers with different outcomes."""
        crawled_ok = _make_crawled(source_id="2401.00001", title="New Paper")
        crawled_dup = _make_crawled(source_id="2401.00002", title="Dup Paper")
        existing = Paper(id=5, source="arxiv", source_id="2401.00002", title="Dup", status="ready")

        async def mock_fetch(paper_id: str) -> CrawledPaper | None:
            if paper_id == "2401.00001":
                return crawled_ok
            if paper_id == "2401.00002":
                return crawled_dup
            return None  # "9999.99999" → not_found

        mock_crawler = AsyncMock()
        mock_crawler.fetch_paper_by_id.side_effect = mock_fetch

        call_count = 0

        def mock_scalar_one_or_none() -> Paper | None:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return None  # first paper is new
            return existing  # second paper is duplicate

        mock_db_result = MagicMock()
        mock_db_result.scalar_one_or_none.side_effect = mock_scalar_one_or_none

        db = AsyncMock()
        db.execute.return_value = mock_db_result

        with patch("daily_ai_papers.services.submission._get_crawler", return_value=mock_crawler):
            results = await submit_papers(
                "arxiv", ["2401.00001", "2401.00002", "9999.99999"], db
            )

        statuses = {r.source_id: r.status for r in results}
        assert statuses["2401.00001"] == "queued"
        assert statuses["2401.00002"] == "duplicate"
        assert statuses["9999.99999"] == "not_found"

    @pytest.mark.asyncio
    async def test_unsupported_source_raises(self) -> None:
        db = AsyncMock()
        with pytest.raises(ValueError, match="Unsupported paper source"):
            await submit_papers("unknown_source", ["123"], db)
