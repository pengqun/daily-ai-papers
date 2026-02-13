"""LLM-based translation service for paper content."""

import logging

from daily_ai_papers.services.llm_client import llm_complete

logger = logging.getLogger(__name__)

LANGUAGE_NAMES = {
    "zh": "Chinese",
    "ja": "Japanese",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "ko": "Korean",
}

SYSTEM_PROMPT = "You are a professional academic translator."

TRANSLATION_PROMPT = """\
Translate the following academic paper text into {language_name}.

Requirements:
- Preserve all technical terms and proper nouns
- Maintain an academic tone
- Keep the original structure (paragraphs, lists)
- Do NOT add any commentary — output ONLY the translation

Text to translate:
---
{text}
---
"""


async def translate_text(text: str, target_language: str) -> str:
    """Translate text into the target language using an LLM.

    Args:
        text: The text to translate.
        target_language: Language code (e.g. "zh", "ja", "es").

    Returns:
        The translated text.
    """
    language_name = LANGUAGE_NAMES.get(target_language, target_language)
    prompt = TRANSLATION_PROMPT.format(language_name=language_name, text=text)

    logger.info("Translating %d chars to %s", len(text), language_name)
    result = await llm_complete(prompt, system=SYSTEM_PROMPT)
    logger.info("Translation complete: %d chars -> %d chars (%s)", len(text), len(result), language_name)
    return result.strip()
