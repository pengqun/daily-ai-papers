"""Tests for LLM-powered features using the 'fake' provider.

These tests exercise the full code path (metadata extraction, translation,
end-to-end pipeline) WITHOUT requiring an API key. They use LLM_PROVIDER=fake
which returns canned but structurally-valid responses.

This ensures:
- The prompt templates produce parsable output
- The JSON parsing / extraction logic works correctly
- The pipeline wiring (crawl -> parse -> analyze -> translate) is sound
- CI can run all tests without any secrets configured
"""

import os

import pytest

from daily_ai_papers.config import settings
from daily_ai_papers.services.crawler.arxiv import ArxivCrawler
from daily_ai_papers.services.llm_client import llm_complete, parse_json_response
from daily_ai_papers.services.parser.metadata_extractor import extract_metadata
from daily_ai_papers.services.parser.pdf_extractor import download_pdf, extract_text_from_pdf
from daily_ai_papers.services.translator import translate_text

from .conftest import KNOWN_ARXIV_ID, SAMPLE_ABSTRACT


@pytest.fixture(autouse=True)
def _use_fake_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch settings to use the fake LLM provider for every test in this module."""
    monkeypatch.setattr(settings, "llm_provider", "fake")
    monkeypatch.setattr(settings, "llm_api_key", "")


class TestFakeLLMClient:
    """Verify the fake provider returns valid responses."""

    @pytest.mark.asyncio
    async def test_simple_completion(self) -> None:
        response = await llm_complete("What is 2+3?")
        assert "5" in response
        print(f"\n  Fake LLM response: {response!r}")

    @pytest.mark.asyncio
    async def test_json_response(self) -> None:
        response = await llm_complete("Give me JSON", response_json=True)
        data = parse_json_response(response)
        assert isinstance(data, dict)
        print(f"\n  Fake JSON: {data}")


class TestFakeMetadataExtraction:
    """Test metadata extraction with fake LLM."""

    @pytest.mark.asyncio
    async def test_extract_metadata(self) -> None:
        meta = await extract_metadata(SAMPLE_ABSTRACT)

        assert len(meta.summary) > 50
        assert "Transformer" in meta.summary
        assert len(meta.contributions) >= 2
        assert len(meta.keywords) >= 5
        assert len(meta.methodology) > 10
        assert len(meta.results) > 10

        print(f"\n  Summary: {meta.summary[:100]}...")
        print(f"  Keywords: {meta.keywords}")
        print(f"  Contributions ({len(meta.contributions)}): {meta.contributions[0][:60]}...")


class TestFakeTranslation:
    """Test translation with fake LLM."""

    @pytest.mark.asyncio
    async def test_translate_to_chinese(self) -> None:
        result = await translate_text("Attention is all you need.", "zh")
        assert any("\u4e00" <= ch <= "\u9fff" for ch in result)
        print(f"\n  Chinese: {result}")

    @pytest.mark.asyncio
    async def test_translate_to_japanese(self) -> None:
        result = await translate_text("Attention is all you need.", "ja")
        has_jp = any(
            ("\u3040" <= ch <= "\u309f")
            or ("\u30a0" <= ch <= "\u30ff")
            or ("\u4e00" <= ch <= "\u9fff")
            for ch in result
        )
        assert has_jp
        print(f"\n  Japanese: {result}")


class TestFakeE2EPipeline:
    """End-to-end: crawl -> PDF -> parse -> fake-LLM analyze -> fake-LLM translate."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self) -> None:
        pytest.importorskip("fitz", reason="PyMuPDF not installed")

        # Step 1: Crawl (real arXiv call)
        crawler = ArxivCrawler()
        paper = await crawler.fetch_paper_by_id(KNOWN_ARXIV_ID)
        assert paper is not None
        print(f"\n  [Step 1] Crawled: {paper.title}")

        # Step 2: Download & parse PDF (real download)
        pdf_path = await download_pdf(paper.pdf_url)
        try:
            text = extract_text_from_pdf(pdf_path)
            assert len(text) > 1000
            print(f"  [Step 2] Extracted {len(text):,} chars")
        finally:
            os.unlink(pdf_path)

        # Step 3: LLM metadata extraction (fake)
        meta = await extract_metadata(text)
        assert meta.summary
        assert meta.keywords
        print(f"  [Step 3] Summary: {meta.summary[:80]}...")
        print(f"           Keywords: {meta.keywords[:5]}")

        # Step 4: Translation (fake)
        summary_zh = await translate_text(meta.summary, "zh")
        assert any("\u4e00" <= ch <= "\u9fff" for ch in summary_zh)
        print(f"  [Step 4] Chinese: {summary_zh}")
