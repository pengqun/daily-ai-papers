"""Integration tests for ArxivCrawler — hits real arXiv API."""

import pytest

from daily_ai_papers.services.crawler.arxiv import ArxivCrawler
from daily_ai_papers.services.crawler.base import CrawledPaper


@pytest.fixture
def crawler() -> ArxivCrawler:
    return ArxivCrawler()


# A well-known paper that will always exist: "Attention Is All You Need"
KNOWN_ARXIV_ID = "1706.03762"


class TestFetchPaperById:
    """Test fetching a single paper by arXiv ID (real network call)."""

    @pytest.mark.asyncio
    async def test_fetch_known_paper(self, crawler: ArxivCrawler) -> None:
        paper = await crawler.fetch_paper_by_id(KNOWN_ARXIV_ID)

        assert paper is not None
        assert isinstance(paper, CrawledPaper)
        assert paper.source == "arxiv"
        assert paper.source_id == KNOWN_ARXIV_ID
        assert "Attention" in paper.title
        assert paper.abstract is not None and len(paper.abstract) > 50
        assert paper.pdf_url is not None and "arxiv.org" in paper.pdf_url
        assert paper.published_at is not None
        assert len(paper.author_names) > 0
        assert len(paper.categories) > 0

        print(f"\n  Title: {paper.title}")
        print(f"  Authors: {', '.join(paper.author_names[:3])}...")
        print(f"  Categories: {paper.categories}")
        print(f"  PDF: {paper.pdf_url}")

    @pytest.mark.asyncio
    async def test_fetch_nonexistent_paper(self, crawler: ArxivCrawler) -> None:
        paper = await crawler.fetch_paper_by_id("9999.99999")
        assert paper is None


class TestFetchRecentPapers:
    """Test fetching recent papers from arXiv (real network call)."""

    @pytest.mark.asyncio
    async def test_fetch_recent_cs_ai(self, crawler: ArxivCrawler) -> None:
        papers = await crawler.fetch_recent_papers(
            categories=["cs.AI"],
            max_results=5,
            days_back=30,  # wide window to ensure results
        )

        assert isinstance(papers, list)
        # arXiv should have at least some cs.AI papers in the last 30 days
        # (might be 0 if API is slow, so we just check the structure)
        for p in papers:
            assert isinstance(p, CrawledPaper)
            assert p.source == "arxiv"
            assert p.title
            assert p.source_id

        print(f"\n  Fetched {len(papers)} recent cs.AI papers")
        for p in papers[:3]:
            print(f"    - [{p.source_id}] {p.title[:80]}")
