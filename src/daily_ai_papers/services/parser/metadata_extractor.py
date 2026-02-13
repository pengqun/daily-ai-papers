"""LLM-based metadata extraction from paper text."""

import logging
from dataclasses import dataclass, field

from daily_ai_papers.services.llm_client import llm_complete, parse_json_response

logger = logging.getLogger(__name__)

_MAX_TEXT_CHARS = 12_000  # truncate very long papers to stay within context limits

SYSTEM_PROMPT = "You are a research paper analyst. Always respond in valid JSON."

EXTRACTION_PROMPT = """\
Given the following paper text, extract structured metadata.

Return a JSON object with exactly these fields:
- "summary": A concise 3-5 sentence summary of the paper
- "contributions": A list of the paper's main contributions (2-5 items)
- "keywords": A list of relevant keywords (5-10 items)
- "methodology": A brief description of the approach/method used
- "results": Key findings or results

Paper text (possibly truncated):
---
{text}
---

Respond ONLY with the JSON object, no extra text.
"""


@dataclass
class ExtractedMetadata:
    summary: str = ""
    contributions: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    methodology: str = ""
    results: str = ""


async def extract_metadata(paper_text: str) -> ExtractedMetadata:
    """Use an LLM to extract structured metadata from paper text."""
    truncated = paper_text[:_MAX_TEXT_CHARS]
    prompt = EXTRACTION_PROMPT.format(text=truncated)

    logger.info(
        "Extracting metadata via LLM (%d chars input, truncated=%s)",
        len(paper_text),
        len(paper_text) > _MAX_TEXT_CHARS,
    )

    raw = await llm_complete(prompt, system=SYSTEM_PROMPT, response_json=True)
    data = parse_json_response(raw)

    return ExtractedMetadata(
        summary=data.get("summary", ""),
        contributions=data.get("contributions", []),
        keywords=data.get("keywords", []),
        methodology=data.get("methodology", ""),
        results=data.get("results", ""),
    )
