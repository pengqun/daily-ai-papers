"""Paper submission service — handles manually submitted paper IDs."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from daily_ai_papers.models.paper import Paper
from daily_ai_papers.schemas.paper import SubmitPaperResult
from daily_ai_papers.services.crawler.arxiv import ArxivCrawler
from daily_ai_papers.services.crawler.base import BaseCrawler, CrawledPaper

logger = logging.getLogger(__name__)

# Registry of crawlers keyed by source name.  Extend when adding new sources.
_CRAWLERS: dict[str, BaseCrawler] = {
    "arxiv": ArxivCrawler(),
}


def _get_crawler(source: str) -> BaseCrawler:
    crawler = _CRAWLERS.get(source)
    if crawler is None:
        raise ValueError(f"Unsupported paper source: {source}")
    return crawler


async def _upsert_paper(db: AsyncSession, crawled: CrawledPaper) -> tuple[Paper, bool]:
    """Insert a paper if it doesn't exist yet; return (paper, is_new)."""
    stmt = select(Paper).where(
        Paper.source == crawled.source,
        Paper.source_id == crawled.source_id,
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing is not None:
        return existing, False

    paper = Paper(
        source=crawled.source,
        source_id=crawled.source_id,
        title=crawled.title,
        abstract=crawled.abstract,
        pdf_url=crawled.pdf_url,
        published_at=crawled.published_at,
        categories=crawled.categories,
        status="crawled",
    )
    db.add(paper)
    await db.flush()  # populate paper.id
    return paper, True


async def submit_papers(
    source: str,
    paper_ids: list[str],
    db: AsyncSession,
) -> list[SubmitPaperResult]:
    """Fetch metadata for each paper ID and store in the database.

    For each submitted ID the result is one of:
    - **queued** — new paper created, ready for downstream processing
    - **duplicate** — paper already existed in the database
    - **not_found** — source API returned no result for this ID
    - **error** — unexpected failure when fetching this ID
    """
    crawler = _get_crawler(source)
    results: list[SubmitPaperResult] = []

    for pid in paper_ids:
        try:
            crawled = await crawler.fetch_paper_by_id(pid)

            if crawled is None:
                results.append(
                    SubmitPaperResult(
                        source_id=pid,
                        status="not_found",
                        message=f"Paper {pid} not found on {source}",
                    )
                )
                continue

            paper, is_new = await _upsert_paper(db, crawled)

            if is_new:
                results.append(
                    SubmitPaperResult(
                        source_id=pid,
                        status="queued",
                        paper_id=paper.id,
                        message=f"Paper queued for processing: {crawled.title}",
                    )
                )
            else:
                results.append(
                    SubmitPaperResult(
                        source_id=pid,
                        status="duplicate",
                        paper_id=paper.id,
                        message=f"Paper already exists (id={paper.id})",
                    )
                )

        except Exception:
            logger.exception("Failed to fetch paper %s from %s", pid, source)
            results.append(
                SubmitPaperResult(
                    source_id=pid,
                    status="error",
                    message=f"Failed to fetch paper {pid} from {source}",
                )
            )

    await db.commit()

    queued = sum(1 for r in results if r.status == "queued")
    skipped = len(results) - queued
    logger.info("Submitted %d paper(s): %d queued, %d skipped", len(results), queued, skipped)
    return results
