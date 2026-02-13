"""LLM-based metadata extraction from paper text."""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """\
You are a research paper analyst. Given the following paper text, extract structured metadata.

Return a JSON object with these fields:
- "summary": A concise 3-5 sentence summary of the paper
- "contributions": A list of the paper's main contributions (2-5 items)
- "keywords": A list of relevant keywords (5-10 items)
- "methodology": A brief description of the approach/method used
- "results": Key findings or results

Paper text:
{text}
"""


@dataclass
class ExtractedMetadata:
    summary: str = ""
    contributions: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    methodology: str = ""
    results: str = ""


async def extract_metadata(paper_text: str) -> ExtractedMetadata:
    """Use an LLM to extract structured metadata from paper text.

    TODO: Implement LLM call in Phase 3. Currently returns a placeholder.
    """
    logger.info("Metadata extraction called with %d chars of text", len(paper_text))
    return ExtractedMetadata()
