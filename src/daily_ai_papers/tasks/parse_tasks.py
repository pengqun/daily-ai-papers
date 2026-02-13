"""Celery tasks for paper parsing and analysis."""

import logging

from daily_ai_papers.tasks.celery_app import app

logger = logging.getLogger(__name__)


@app.task(name="daily_ai_papers.tasks.parse_tasks.parse_paper")  # type: ignore[untyped-decorator]
def parse_paper(paper_id: int) -> dict[str, str]:
    """Download, parse, and analyze a single paper.

    TODO: Implement in Phase 3:
    1. Download PDF from paper.pdf_url
    2. Extract full text via PyMuPDF
    3. Run LLM metadata extraction (summary, contributions, keywords)
    4. Update paper record in database
    5. Dispatch embedding task
    """
    logger.info("parse_paper task triggered for paper_id=%d", paper_id)
    return {"paper_id": str(paper_id), "status": "not_implemented"}
