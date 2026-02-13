"""PDF download and text extraction."""

import logging
import tempfile
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)


async def download_pdf(url: str) -> Path:
    """Download a PDF from a URL to a temporary file."""
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()

    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.write(response.content)
    tmp.close()
    return Path(tmp.name)


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract full text from a PDF file using PyMuPDF."""
    import fitz  # PyMuPDF — lazy import to keep download_pdf usable without it

    doc = fitz.open(str(pdf_path))
    text_parts: list[str] = []

    for page in doc:
        text_parts.append(page.get_text())

    doc.close()
    full_text = "\n".join(text_parts)
    logger.info("Extracted %d characters from %s", len(full_text), pdf_path.name)
    return full_text
