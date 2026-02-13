"""Tests for LLM-powered features using the 'fake' provider.

These tests exercise the full code path (metadata extraction, translation,
end-to-end pipeline) WITHOUT requiring an API key. They use LLM_PROVIDER=fake
which returns canned but structurally-valid responses.

This ensures:
- The prompt templates produce parsable output
- The JSON parsing / extraction logic works correctly
- The pipeline wiring (crawl → parse → analyze → translate) is sound
- CI can run all tests without any secrets configured
"""

import os
from unittest.mock import patch

import pytest


def _fake_env(**overrides: str):
    """Patch environment + settings to use the fake LLM provider."""
    env = {"LLM_PROVIDER": "fake", "LLM_API_KEY": "", **overrides}
    return patch.dict(os.environ, env)


SAMPLE_ABSTRACT = (
    "The dominant sequence transduction models are based on complex recurrent or "
    "convolutional neural networks that include an encoder and a decoder. The best "
    "performing models also connect the encoder and decoder through an attention "
    "mechanism. We propose a new simple network architecture, the Transformer, "
    "based solely on attention mechanisms, dispensing with recurrence and convolutions "
    "entirely. Experiments on two machine translation tasks show these models to "
    "be superior in quality while being more parallelizable and requiring significantly "
    "less time to train."
)


class TestFakeLLMClient:
    """Verify the fake provider returns valid responses."""

    @pytest.mark.asyncio
    async def test_simple_completion(self) -> None:
        with _fake_env():
            from importlib import reload

            import daily_ai_papers.config as cfg

            reload(cfg)
            from daily_ai_papers.services.llm_client import llm_complete

            response = await llm_complete("What is 2+3?")
            assert "5" in response
            print(f"\n  Fake LLM response: {response!r}")

    @pytest.mark.asyncio
    async def test_json_response(self) -> None:
        with _fake_env():
            from importlib import reload

            import daily_ai_papers.config as cfg

            reload(cfg)
            from daily_ai_papers.services.llm_client import llm_complete, parse_json_response

            response = await llm_complete("Give me JSON", response_json=True)
            data = parse_json_response(response)
            assert isinstance(data, dict)
            print(f"\n  Fake JSON: {data}")


class TestFakeMetadataExtraction:
    """Test metadata extraction with fake LLM."""

    @pytest.mark.asyncio
    async def test_extract_metadata(self) -> None:
        with _fake_env():
            from importlib import reload

            import daily_ai_papers.config as cfg

            reload(cfg)
            from daily_ai_papers.services.parser.metadata_extractor import extract_metadata

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
        with _fake_env():
            from importlib import reload

            import daily_ai_papers.config as cfg

            reload(cfg)
            from daily_ai_papers.services.translator import translate_text

            result = await translate_text("Attention is all you need.", "zh")
            assert any("\u4e00" <= ch <= "\u9fff" for ch in result)
            print(f"\n  Chinese: {result}")

    @pytest.mark.asyncio
    async def test_translate_to_japanese(self) -> None:
        with _fake_env():
            from importlib import reload

            import daily_ai_papers.config as cfg

            reload(cfg)
            from daily_ai_papers.services.translator import translate_text

            result = await translate_text("Attention is all you need.", "ja")
            has_jp = any(
                ("\u3040" <= ch <= "\u309f") or ("\u30a0" <= ch <= "\u30ff") or ("\u4e00" <= ch <= "\u9fff")
                for ch in result
            )
            assert has_jp
            print(f"\n  Japanese: {result}")


class TestFakeE2EPipeline:
    """End-to-end: crawl → PDF → parse → fake-LLM analyze → fake-LLM translate."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self) -> None:
        with _fake_env():
            from importlib import reload

            import daily_ai_papers.config as cfg

            reload(cfg)

            from daily_ai_papers.services.crawler.arxiv import ArxivCrawler
            from daily_ai_papers.services.parser.metadata_extractor import extract_metadata
            from daily_ai_papers.services.parser.pdf_extractor import (
                download_pdf,
                extract_text_from_pdf,
            )
            from daily_ai_papers.services.translator import translate_text

            # Step 1: Crawl (real arXiv call)
            crawler = ArxivCrawler()
            paper = await crawler.fetch_paper_by_id("1706.03762")
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

            print("\n  ✓ Full pipeline completed successfully (crawl=real, LLM=fake)")
