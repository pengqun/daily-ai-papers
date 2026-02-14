"""Unit tests for Celery tasks.

Tests task logic with mocked crawlers — no Celery broker needed.
"""

from unittest.mock import AsyncMock, patch

import pytest

from daily_ai_papers.services.crawler.base import CrawledPaper
from daily_ai_papers.tasks.parse_tasks import parse_paper


class TestParsePaperStub:
    """Test the parse_paper task stub."""

    def test_returns_not_implemented(self) -> None:
        result = parse_paper(42)
        assert result == {"paper_id": "42", "status": "not_implemented"}

    def test_returns_correct_paper_id(self) -> None:
        result = parse_paper(7)
        assert result["paper_id"] == "7"


class TestFetchSubmittedPaper:
    """Test the fetch_submitted_paper task logic.

    fetch_submitted_paper is a bound Celery task (bind=True), so calling
    it directly via __call__ auto-injects self. We use that for simple
    cases, and .run(self, ...) when we need to mock self.retry().
    """

    def test_unknown_source_returns_error(self) -> None:
        from daily_ai_papers.tasks.crawl_tasks import fetch_submitted_paper

        result = fetch_submitted_paper("unknown_source", "123")
        assert result["status"] == "error"
        assert "Unknown source" in result["message"]

    def test_paper_not_found_returns_not_found(self) -> None:
        from daily_ai_papers.tasks.crawl_tasks import fetch_submitted_paper

        mock_crawler = AsyncMock()

        with (
            patch(
                "daily_ai_papers.services.submission._get_crawler", return_value=mock_crawler
            ),
            patch("asyncio.run", return_value=None),
        ):
            result = fetch_submitted_paper("arxiv", "9999.99999")

        assert result["status"] == "not_found"
        assert result["source_id"] == "9999.99999"

    def test_successful_fetch_returns_fetched(self) -> None:
        from daily_ai_papers.tasks.crawl_tasks import fetch_submitted_paper

        crawled = CrawledPaper(
            source="arxiv",
            source_id="2401.00001",
            title="A Great Paper",
        )
        mock_crawler = AsyncMock()

        with (
            patch(
                "daily_ai_papers.services.submission._get_crawler", return_value=mock_crawler
            ),
            patch("asyncio.run", return_value=crawled),
        ):
            result = fetch_submitted_paper("arxiv", "2401.00001")

        assert result["status"] == "fetched"
        assert result["title"] == "A Great Paper"

    def test_fetch_exception_triggers_retry(self) -> None:
        from daily_ai_papers.tasks.crawl_tasks import fetch_submitted_paper

        mock_crawler = AsyncMock()

        # Patch the task object's retry method directly
        with (
            patch.object(
                fetch_submitted_paper, "retry", side_effect=RuntimeError("retry called")
            ) as mock_retry,
            patch(
                "daily_ai_papers.services.submission._get_crawler", return_value=mock_crawler
            ),
            patch("asyncio.run", side_effect=ConnectionError("network down")),
            pytest.raises(RuntimeError, match="retry called"),
        ):
            fetch_submitted_paper("arxiv", "2401.00001")

        mock_retry.assert_called_once()


class TestCrawlAllSources:
    """Test the crawl_all_sources task stub."""

    def test_returns_zero_papers(self) -> None:
        from daily_ai_papers.tasks.crawl_tasks import crawl_all_sources

        result = crawl_all_sources()
        assert result == {"new_papers": 0}
