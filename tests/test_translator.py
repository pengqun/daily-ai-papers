"""Unit tests for the translation service.

Covers language codes not exercised by test_fake_llm.py.
"""

import pytest

from daily_ai_papers.config import settings
from daily_ai_papers.services.translator import LANGUAGE_NAMES, translate_text


@pytest.fixture(autouse=True)
def _use_fake_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "llm_provider", "fake")
    monkeypatch.setattr(settings, "llm_api_key", "")


class TestTranslateText:
    """Test translate_text with the fake LLM provider."""

    @pytest.mark.asyncio
    async def test_translate_to_spanish(self) -> None:
        result = await translate_text("Attention is all you need.", "es")
        assert len(result) > 0
        # The fake provider returns "Traducción simulada..." for other languages
        assert "Traducci" in result

    @pytest.mark.asyncio
    async def test_unknown_language_code_uses_code_as_name(self) -> None:
        """When the language code isn't in LANGUAGE_NAMES, it's used as-is."""
        assert "xx" not in LANGUAGE_NAMES
        # Should still call llm_complete without error (fake provider handles it)
        result = await translate_text("Hello world.", "xx")
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_result_is_stripped(self) -> None:
        result = await translate_text("Test.", "zh")
        assert result == result.strip()
