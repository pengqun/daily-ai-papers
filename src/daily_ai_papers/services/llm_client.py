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
    provider = settings.llm_provider
    model = model or settings.llm_model

    if provider == "fake":
        return _fake_complete(prompt, response_json)

    api_key = settings.llm_api_key
    if not api_key:
        raise RuntimeError(
            "LLM_API_KEY is not set. Configure it in .env or as an environment variable."
        )

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

    client_kwargs: dict[str, Any] = {"api_key": api_key}
    base_url = settings.llm_base_url
    if base_url:
        client_kwargs["base_url"] = base_url

    client = AsyncOpenAI(**client_kwargs)
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
    label = base_url or "OpenAI"
    logger.info("%s %s responded with %d chars", label, model, len(text))
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


def _fake_complete(prompt: str, response_json: bool) -> str:
    """Return canned responses for testing without an LLM API key.

    Recognises prompts from metadata_extractor and translator by keyword
    matching and returns structurally-valid responses so the full pipeline
    can be exercised offline.
    """
    prompt_lower = prompt.lower()

    # Metadata extraction prompt
    if "extract structured metadata" in prompt_lower or "contributions" in prompt_lower and "keywords" in prompt_lower:
        return json.dumps({
            "summary": (
                "This paper proposes the Transformer, a novel architecture based entirely "
                "on attention mechanisms. It eliminates recurrence and convolutions, achieving "
                "state-of-the-art results on machine translation benchmarks while being more "
                "parallelizable and faster to train."
            ),
            "contributions": [
                "Introduced the Transformer architecture based solely on attention",
                "Achieved new SOTA on WMT 2014 English-to-German and English-to-French translation",
                "Demonstrated superior training efficiency compared to recurrent models",
            ],
            "keywords": [
                "transformer", "attention mechanism", "self-attention",
                "machine translation", "sequence-to-sequence", "neural network",
                "encoder-decoder", "multi-head attention",
            ],
            "methodology": (
                "The Transformer uses stacked self-attention and point-wise fully connected "
                "layers for both encoder and decoder, replacing recurrence entirely."
            ),
            "results": (
                "The model achieved 28.4 BLEU on WMT 2014 English-to-German and 41.8 BLEU "
                "on English-to-French, surpassing all previous single models and ensembles."
            ),
        })

    # Translation prompt (Chinese)
    if "chinese" in prompt_lower or "中文" in prompt_lower:
        return "我们提出了一种新的网络架构——Transformer，完全基于注意力机制。"

    # Translation prompt (Japanese)
    if "japanese" in prompt_lower or "日本語" in prompt_lower:
        return "注意力こそが全てである。"

    # Translation prompt (other languages)
    if "translate" in prompt_lower:
        return "Traducción simulada del texto original para pruebas."

    # Fallback
    if response_json:
        return json.dumps({"answer": "fake response", "status": "ok"})
    return "5"


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
