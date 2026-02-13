"""Integration tests for LLM-powered features.

These tests make real API calls to OpenAI or Anthropic.
They are automatically SKIPPED when LLM_API_KEY is not set.

To run:
    LLM_API_KEY=sk-... python -m pytest tests/test_llm_integration.py -v -s

You can also set LLM_PROVIDER (default: "openai") and LLM_MODEL to control
which provider/model is used.
"""

import os

import pytest

from daily_ai_papers.config import settings

from .conftest import SAMPLE_ABSTRACT

# ── Skip guard ──────────────────────────────────────────────────────────────
_has_llm_key = bool(settings.llm_api_key or os.environ.get("LLM_API_KEY"))

pytestmark = pytest.mark.skipif(
    not _has_llm_key,
    reason="LLM_API_KEY not set — skipping LLM integration tests",
)


# ── LLM client ──────────────────────────────────────────────────────────────


class TestLLMClient:
    """Test the low-level llm_complete function."""

    @pytest.mark.asyncio
    async def test_simple_completion(self) -> None:
        from daily_ai_papers.services.llm_client import llm_complete

        response = await llm_complete(
            "What is 2 + 3? Reply with just the number.",
            temperature=0.0,
            max_tokens=16,
        )
        assert "5" in response
        print(f"\n  LLM response: {response.strip()!r}")

    @pytest.mark.asyncio
    async def test_json_response(self) -> None:
        from daily_ai_papers.services.llm_client import llm_complete, parse_json_response

        response = await llm_complete(
            'Return a JSON object: {"greeting": "hello"}. Only output JSON.',
            system="You are a helpful assistant. Always respond in valid JSON.",
            response_json=True,
            max_tokens=64,
        )
        data = parse_json_response(response)
        assert "greeting" in data
        print(f"\n  Parsed JSON: {data}")


# ── Metadata extraction ────────────────────────────────────────────────────


class TestMetadataExtraction:
    """Test LLM-based metadata extraction on a real abstract."""

    @pytest.mark.asyncio
    async def test_extract_metadata_from_abstract(self) -> None:
        from daily_ai_papers.services.parser.metadata_extractor import extract_metadata

        meta = await extract_metadata(SAMPLE_ABSTRACT)

        # Summary should be non-empty and mention the paper's topic
        assert len(meta.summary) > 50
        assert any(kw in meta.summary.lower() for kw in ["transformer", "attention", "translation"])

        # Should have at least 1 contribution and 3 keywords
        assert len(meta.contributions) >= 1
        assert len(meta.keywords) >= 3

        # Methodology and results should be filled
        assert len(meta.methodology) > 10
        assert len(meta.results) > 10

        print(f"\n  Summary: {meta.summary[:120]}...")
        print(f"  Contributions: {meta.contributions}")
        print(f"  Keywords: {meta.keywords}")
        print(f"  Methodology: {meta.methodology[:100]}...")
        print(f"  Results: {meta.results[:100]}...")


# ── Translation ─────────────────────────────────────────────────────────────


class TestTranslation:
    """Test LLM-based translation."""

    @pytest.mark.asyncio
    async def test_translate_to_chinese(self) -> None:
        from daily_ai_papers.services.translator import translate_text

        short_text = (
            "We propose a new network architecture, the Transformer, "
            "based solely on attention mechanisms."
        )
        translated = await translate_text(short_text, "zh")

        # Should contain Chinese characters
        assert any("\u4e00" <= ch <= "\u9fff" for ch in translated), (
            f"Expected Chinese characters, got: {translated[:100]}"
        )
        assert len(translated) > 10

        print(f"\n  Original:   {short_text}")
        print(f"  Translated: {translated}")

    @pytest.mark.asyncio
    async def test_translate_to_japanese(self) -> None:
        from daily_ai_papers.services.translator import translate_text

        short_text = "Attention is all you need."
        translated = await translate_text(short_text, "ja")

        # Should contain Japanese characters (Hiragana/Katakana/Kanji)
        has_jp = any(
            ("\u3040" <= ch <= "\u309f")  # Hiragana
            or ("\u30a0" <= ch <= "\u30ff")  # Katakana
            or ("\u4e00" <= ch <= "\u9fff")  # Kanji
            for ch in translated
        )
        assert has_jp, f"Expected Japanese characters, got: {translated[:100]}"

        print(f"\n  Original:   {short_text}")
        print(f"  Translated: {translated}")
