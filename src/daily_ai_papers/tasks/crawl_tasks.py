"""Celery tasks for paper crawling."""

import logging

from daily_ai_papers.tasks.celery_app import app

logger = logging.getLogger(__name__)


@app.task(name="daily_ai_papers.tasks.crawl_tasks.crawl_all_sources")
def crawl_all_sources() -> dict[str, int]:
    """Crawl papers from all configured sources.

    TODO: Implement in Phase 2:
    1. Instantiate each crawler (ArxivCrawler, etc.)
    2. Fetch recent papers
    3. Deduplicate against existing records
    4. Store new papers in database with status='crawled'
    5. Dispatch parse tasks for each new paper
    """
    logger.info("crawl_all_sources task triggered")
    return {"new_papers": 0}


@app.task(
    name="daily_ai_papers.tasks.crawl_tasks.fetch_submitted_paper",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def fetch_submitted_paper(self, source: str, source_id: str) -> dict[str, str]:  # type: ignore[no-untyped-def]
    """Async Celery task: fetch & process a single manually-submitted paper.

    This task is dispatched after a paper is submitted via the API. It runs
    the full pipeline: fetch metadata → download PDF → parse → analyze.

    Args:
        source: Paper source name (e.g. "arxiv").
        source_id: Source-specific paper ID (e.g. "2401.00001").
    """
    import asyncio

    from daily_ai_papers.services.submission import _get_crawler

    try:
        crawler = _get_crawler(source)
    except ValueError:
        return {"source_id": source_id, "status": "error", "message": f"Unknown source: {source}"}

    try:
        paper = asyncio.run(crawler.fetch_paper_by_id(source_id))
    except Exception as exc:
        logger.exception("Failed to fetch %s:%s", source, source_id)
        raise self.retry(exc=exc)

    if paper is None:
        return {"source_id": source_id, "status": "not_found"}

    logger.info("Fetched submitted paper %s:%s — %s", source, source_id, paper.title)
    # TODO: chain into parse_paper task once Phase 3 is implemented
    return {"source_id": source_id, "status": "fetched", "title": paper.title}
