"""Unit tests for the LLM client module.

Covers parse_json_response edge cases and provider validation errors.
"""

import json

import pytest

from daily_ai_papers.config import settings
from daily_ai_papers.services.llm_client import llm_complete, parse_json_response


class TestParseJsonResponse:
    """Test JSON extraction from LLM responses."""

    def test_plain_json(self) -> None:
        raw = json.dumps({"key": "value", "count": 42})
        assert parse_json_response(raw) == {"key": "value", "count": 42}

    def test_json_with_language_fence(self) -> None:
        raw = '```json\n{"key": "value"}\n```'
        assert parse_json_response(raw) == {"key": "value"}

    def test_json_with_bare_fence(self) -> None:
        raw = '```\n{"key": "value"}\n```'
        assert parse_json_response(raw) == {"key": "value"}

    def test_json_with_surrounding_whitespace(self) -> None:
        raw = '  \n {"key": "value"} \n  '
        assert parse_json_response(raw) == {"key": "value"}

    def test_multiline_json_in_fence(self) -> None:
        raw = '```json\n{\n  "summary": "test",\n  "keywords": ["a", "b"]\n}\n```'
        result = parse_json_response(raw)
        assert result["summary"] == "test"
        assert result["keywords"] == ["a", "b"]

    def test_invalid_json_raises(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            parse_json_response("this is not json")

    def test_empty_string_raises(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            parse_json_response("")

    def test_empty_fences_raise(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            parse_json_response("```json\n```")


class TestLlmCompleteProviderValidation:
    """Test provider routing and error handling."""

    @pytest.mark.asyncio
    async def test_unsupported_provider_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "llm_provider", "not_a_provider")
        monkeypatch.setattr(settings, "llm_api_key", "fake-key")
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            await llm_complete("hello")

    @pytest.mark.asyncio
    async def test_openai_without_api_key_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "llm_provider", "openai")
        monkeypatch.setattr(settings, "llm_api_key", "")
        with pytest.raises(RuntimeError, match="LLM_API_KEY is not set"):
            await llm_complete("hello")

    @pytest.mark.asyncio
    async def test_anthropic_without_api_key_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "llm_provider", "anthropic")
        monkeypatch.setattr(settings, "llm_api_key", "")
        with pytest.raises(RuntimeError, match="LLM_API_KEY is not set"):
            await llm_complete("hello")

    @pytest.mark.asyncio
    async def test_fake_provider_needs_no_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "llm_provider", "fake")
        monkeypatch.setattr(settings, "llm_api_key", "")
        result = await llm_complete("What is 2+3?")
        assert result == "5"
