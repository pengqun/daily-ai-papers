"""arXiv paper crawler implementation."""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import feedparser
import httpx

from daily_ai_papers.services.crawler.base import BaseCrawler, CrawledPaper

logger = logging.getLogger(__name__)

ARXIV_API_URL = "https://export.arxiv.org/api/query"


def _parse_datetime(time_struct: Any) -> datetime:
    """Convert a feedparser time struct to a timezone-aware datetime."""
    year, month, day, hour, minute, second = time_struct[:6]
    return datetime(year, month, day, hour, minute, second, tzinfo=UTC)


def _parse_entry(entry: Any, paper_id: str | None = None) -> CrawledPaper:
    """Convert a feedparser entry into a CrawledPaper."""
    published = _parse_datetime(entry.published_parsed)
    pdf_url = next(
        (link.href for link in entry.links if link.get("type") == "application/pdf"),
        None,
    )
    return CrawledPaper(
        source="arxiv",
        source_id=paper_id or entry.id.split("/abs/")[-1],
        title=entry.title.replace("\n", " ").strip(),
        abstract=entry.summary.strip() if entry.summary else None,
        pdf_url=pdf_url,
        published_at=published,
        categories=[tag.term for tag in entry.tags],
        author_names=[a.name for a in entry.authors],
    )


class ArxivCrawler(BaseCrawler):
    """Crawl papers from arXiv using the Atom feed API."""

    async def fetch_recent_papers(
        self,
        categories: list[str],
        max_results: int = 100,
        days_back: int = 1,
    ) -> list[CrawledPaper]:
        cat_query = " OR ".join(f"cat:{cat}" for cat in categories)
        params: dict[str, str | int] = {
            "search_query": cat_query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(ARXIV_API_URL, params=params)
            response.raise_for_status()

        feed = feedparser.parse(response.text)
        cutoff = datetime.now(UTC) - timedelta(days=days_back)
        papers: list[CrawledPaper] = []

        for entry in feed.entries:
            published = _parse_datetime(entry.published_parsed)
            if published < cutoff:
                continue
            papers.append(_parse_entry(entry))

        logger.info("Fetched %d papers from arXiv (categories: %s)", len(papers), categories)
        return papers

    async def fetch_paper_by_id(self, paper_id: str) -> CrawledPaper | None:
        """Fetch a single paper from arXiv by its ID (e.g. '2401.00001')."""
        params: dict[str, str | int] = {
            "id_list": paper_id,
            "max_results": 1,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(ARXIV_API_URL, params=params)
            response.raise_for_status()

        feed = feedparser.parse(response.text)
        if not feed.entries:
            logger.warning("No paper found on arXiv for id=%s", paper_id)
            return None

        entry = feed.entries[0]
        # arXiv returns a stub entry with no title when the ID doesn't exist
        if not getattr(entry, "title", None):
            logger.warning("arXiv returned empty entry for id=%s", paper_id)
            return None

        paper = _parse_entry(entry, paper_id=paper_id)
        logger.info("Fetched paper from arXiv: %s", paper.title)
        return paper
