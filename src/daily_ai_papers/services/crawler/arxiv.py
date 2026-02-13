"""arXiv paper crawler implementation."""

import logging
from datetime import datetime, timedelta, timezone

import feedparser
import httpx

from daily_ai_papers.services.crawler.base import BaseCrawler, CrawledPaper

logger = logging.getLogger(__name__)

ARXIV_API_URL = "https://export.arxiv.org/api/query"


class ArxivCrawler(BaseCrawler):
    """Crawl papers from arXiv using the Atom feed API."""

    async def fetch_recent_papers(
        self,
        categories: list[str],
        max_results: int = 100,
        days_back: int = 1,
    ) -> list[CrawledPaper]:
        cat_query = " OR ".join(f"cat:{cat}" for cat in categories)
        params = {
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
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
        papers: list[CrawledPaper] = []

        for entry in feed.entries:
            published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            if published < cutoff:
                continue

            arxiv_id = entry.id.split("/abs/")[-1]
            pdf_url = next(
                (link.href for link in entry.links if link.get("type") == "application/pdf"),
                None,
            )
            categories_list = [tag.term for tag in entry.tags]

            papers.append(
                CrawledPaper(
                    source="arxiv",
                    source_id=arxiv_id,
                    title=entry.title.replace("\n", " ").strip(),
                    abstract=entry.summary.strip() if entry.summary else None,
                    pdf_url=pdf_url,
                    published_at=published,
                    categories=categories_list,
                    author_names=[a.name for a in entry.authors],
                )
            )

        logger.info("Fetched %d papers from arXiv (categories: %s)", len(papers), categories)
        return papers

    async def fetch_paper_by_id(self, paper_id: str) -> CrawledPaper | None:
        """Fetch a single paper from arXiv by its ID (e.g. '2401.00001')."""
        params = {
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

        published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        pdf_url = next(
            (link.href for link in entry.links if link.get("type") == "application/pdf"),
            None,
        )
        categories_list = [tag.term for tag in entry.tags]

        paper = CrawledPaper(
            source="arxiv",
            source_id=paper_id,
            title=entry.title.replace("\n", " ").strip(),
            abstract=entry.summary.strip() if entry.summary else None,
            pdf_url=pdf_url,
            published_at=published,
            categories=categories_list,
            author_names=[a.name for a in entry.authors],
        )
        logger.info("Fetched paper from arXiv: %s", paper.title)
        return paper
