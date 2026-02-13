"""Unified LLM client supporting OpenAI and Anthropic providers."""

import json
import logging
from typing import Any

from daily_ai_papers.config import settings

logger = logging.getLogger(__name__)


async def llm_complete(
    prompt: str,
    *,
    system: str = "",
    model: str | None = None,
    temperature: float = 0.0,
    max_tokens: int = 2048,
    response_json: bool = False,
) -> str:
    """Send a prompt to the configured LLM provider and return the response text.

    Args:
        prompt: The user message / prompt.
        system: Optional system message.
        model: Override the default model from settings.
        temperature: Sampling temperature.
        max_tokens: Maximum tokens in the response.
        response_json: If True, request JSON output mode (OpenAI only).

    Returns:
        The assistant's text response.

    Raises:
        ValueError: If the configured provider is not supported.
        RuntimeError: If no API key is configured.
    """
    api_key = settings.llm_api_key
    if not api_key:
        raise RuntimeError(
            "LLM_API_KEY is not set. Configure it in .env or as an environment variable."
        )

    provider = settings.llm_provider
    model = model or settings.llm_model

    if provider == "openai":
        return await _openai_complete(
            api_key, model, system, prompt, temperature, max_tokens, response_json
        )
    elif provider == "anthropic":
        return await _anthropic_complete(
            api_key, model, system, prompt, temperature, max_tokens
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


async def _openai_complete(
    api_key: str,
    model: str,
    system: str,
    prompt: str,
    temperature: float,
    max_tokens: int,
    response_json: bool,
) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)
    messages: list[dict[str, Any]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_json:
        kwargs["response_format"] = {"type": "json_object"}

    response = await client.chat.completions.create(**kwargs)
    text = response.choices[0].message.content or ""
    logger.info("OpenAI %s responded with %d chars", model, len(text))
    return text


async def _anthropic_complete(
    api_key: str,
    model: str,
    system: str,
    prompt: str,
    temperature: float,
    max_tokens: int,
) -> str:
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=api_key)
    kwargs: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system

    response = await client.messages.create(**kwargs)
    text = response.content[0].text
    logger.info("Anthropic %s responded with %d chars", model, len(text))
    return text


def parse_json_response(text: str) -> dict[str, Any]:
    """Extract and parse JSON from an LLM response.

    Handles cases where the LLM wraps JSON in ```json ... ``` markdown blocks.
    """
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # Strip markdown code fences
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()
    return json.loads(cleaned)
