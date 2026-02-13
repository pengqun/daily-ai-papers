"""End-to-end pipeline integration test.

Full flow: arXiv crawl → PDF download → text extraction → LLM analysis → translation

The LLM steps are skipped when LLM_API_KEY is not set, but the crawl → parse
portion always runs (only requires network access to arXiv).
"""

import os

import pytest

from daily_ai_papers.config import settings

KNOWN_ARXIV_ID = "1706.03762"  # "Attention Is All You Need"

_has_llm_key = bool(settings.llm_api_key or os.environ.get("LLM_API_KEY"))


@pytest.mark.asyncio
async def test_crawl_and_parse_pipeline() -> None:
    """Crawl a paper from arXiv, download its PDF, and extract full text."""
    from daily_ai_papers.services.crawler.arxiv import ArxivCrawler
    from daily_ai_papers.services.parser.pdf_extractor import (
        download_pdf,
        extract_text_from_pdf,
    )

    # Step 1: Crawl metadata
    crawler = ArxivCrawler()
    paper = await crawler.fetch_paper_by_id(KNOWN_ARXIV_ID)
    assert paper is not None
    assert paper.pdf_url is not None
    print(f"\n  [Step 1] Crawled: {paper.title}")
    print(f"           PDF URL: {paper.pdf_url}")

    # Step 2: Download PDF
    pdf_path = await download_pdf(paper.pdf_url)
    try:
        assert pdf_path.exists()
        size = pdf_path.stat().st_size
        assert size > 10_000
        print(f"  [Step 2] Downloaded PDF: {size:,} bytes")

        # Step 3: Extract text
        text = extract_text_from_pdf(pdf_path)
        assert len(text) > 1000
        assert "attention" in text.lower()
        print(f"  [Step 3] Extracted text: {len(text):,} chars")
    finally:
        os.unlink(pdf_path)


@pytest.mark.asyncio
@pytest.mark.skipif(not _has_llm_key, reason="LLM_API_KEY not set")
async def test_full_pipeline_with_llm() -> None:
    """Full pipeline: crawl → PDF → extract text → LLM analysis → translate."""
    from daily_ai_papers.services.crawler.arxiv import ArxivCrawler
    from daily_ai_papers.services.parser.metadata_extractor import extract_metadata
    from daily_ai_papers.services.parser.pdf_extractor import (
        download_pdf,
        extract_text_from_pdf,
    )
    from daily_ai_papers.services.translator import translate_text

    # Step 1: Crawl
    crawler = ArxivCrawler()
    paper = await crawler.fetch_paper_by_id(KNOWN_ARXIV_ID)
    assert paper is not None
    print(f"\n  [Step 1] Crawled: {paper.title}")

    # Step 2: Download & parse PDF
    pdf_path = await download_pdf(paper.pdf_url)
    try:
        text = extract_text_from_pdf(pdf_path)
        print(f"  [Step 2] Extracted {len(text):,} chars from PDF")
    finally:
        os.unlink(pdf_path)

    # Step 3: LLM metadata extraction
    meta = await extract_metadata(text)
    assert len(meta.summary) > 50
    assert len(meta.keywords) >= 3
    print(f"  [Step 3] Summary: {meta.summary[:120]}...")
    print(f"           Keywords: {meta.keywords}")
    print(f"           Contributions: {meta.contributions}")

    # Step 4: Translate summary to Chinese
    summary_zh = await translate_text(meta.summary, "zh")
    assert len(summary_zh) > 20
    assert any("\u4e00" <= ch <= "\u9fff" for ch in summary_zh)
    print(f"  [Step 4] Chinese summary: {summary_zh[:120]}...")
