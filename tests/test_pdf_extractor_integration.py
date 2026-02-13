"""Integration tests for PDF download and text extraction — real download."""

import os

import pytest

KNOWN_ARXIV_PDF = "https://arxiv.org/pdf/1706.03762"

# Skip if PyMuPDF is not installed (optional heavy dep)
pymupdf_available = True
try:
    import fitz  # noqa: F401
except ImportError:
    pymupdf_available = False


@pytest.mark.asyncio
async def test_download_pdf() -> None:
    """Download a real PDF from arXiv and verify the file exists."""
    from daily_ai_papers.services.parser.pdf_extractor import download_pdf

    path = await download_pdf(KNOWN_ARXIV_PDF)
    try:
        assert path.exists()
        size = path.stat().st_size
        assert size > 10_000, f"PDF too small ({size} bytes), likely not a real PDF"
        print(f"\n  Downloaded PDF: {path} ({size:,} bytes)")
    finally:
        os.unlink(path)


@pytest.mark.asyncio
@pytest.mark.skipif(not pymupdf_available, reason="PyMuPDF not installed")
async def test_download_and_extract_text() -> None:
    """Download a real PDF and extract text from it."""
    from daily_ai_papers.services.parser.pdf_extractor import (
        download_pdf,
        extract_text_from_pdf,
    )

    path = await download_pdf(KNOWN_ARXIV_PDF)
    try:
        text = extract_text_from_pdf(path)
        assert len(text) > 1000, f"Extracted text too short ({len(text)} chars)"
        # "Attention Is All You Need" paper should contain these words
        text_lower = text.lower()
        assert "attention" in text_lower
        assert "transformer" in text_lower

        print(f"\n  Extracted {len(text):,} characters from PDF")
        print(f"  First 200 chars: {text[:200]!r}")
    finally:
        os.unlink(path)
