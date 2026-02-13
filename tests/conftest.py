"""Shared test fixtures and constants."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from daily_ai_papers.main import app

# Well-known paper that will always exist on arXiv
KNOWN_ARXIV_ID = "1706.03762"

SAMPLE_ABSTRACT = (
    "The dominant sequence transduction models are based on complex recurrent or "
    "convolutional neural networks that include an encoder and a decoder. The best "
    "performing models also connect the encoder and decoder through an attention "
    "mechanism. We propose a new simple network architecture, the Transformer, "
    "based solely on attention mechanisms, dispensing with recurrence and convolutions "
    "entirely. Experiments on two machine translation tasks show these models to "
    "be superior in quality while being more parallelizable and requiring significantly "
    "less time to train."
)


@pytest.fixture
async def api_client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client wired to the FastAPI app (no real server needed)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
