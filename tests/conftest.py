"""Shared test fixtures."""

import pytest


@pytest.fixture
def sample_arxiv_entry() -> dict:
    """A sample arXiv paper entry for testing."""
    return {
        "source": "arxiv",
        "source_id": "2401.00001",
        "title": "A Sample Paper on Large Language Models",
        "abstract": "This paper presents a novel approach to improving LLM performance.",
        "pdf_url": "https://arxiv.org/pdf/2401.00001",
        "categories": ["cs.CL", "cs.AI"],
        "author_names": ["Alice Smith", "Bob Jones"],
    }
