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
