"""Paper-related Pydantic schemas."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PaperSource(str, Enum):
    """Supported paper sources."""

    arxiv = "arxiv"
    semantic_scholar = "semantic_scholar"


class AuthorResponse(BaseModel):
    id: int
    name: str
    affiliation: str | None = None

    model_config = {"from_attributes": True}


class PaperListItem(BaseModel):
    id: int
    source: str
    source_id: str
    title: str
    abstract: str | None = None
    published_at: datetime | None = None
    categories: list[str] | None = None
    keywords: list[str] | None = None
    status: str
    authors: list[AuthorResponse] = []

    model_config = {"from_attributes": True}


class PaperDetail(PaperListItem):
    summary: str | None = None
    summary_zh: str | None = None
    contributions: list[str] | None = None
    pdf_url: str | None = None
    created_at: datetime
    updated_at: datetime


class PaperSearchParams(BaseModel):
    query: str | None = None
    categories: list[str] | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    page: int = 1
    page_size: int = 20


# --- Paper submission (manual crawl) ---


class SubmitPaperRequest(BaseModel):
    """Request to manually submit one or more papers for crawling."""

    source: PaperSource = PaperSource.arxiv
    paper_ids: list[str] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of source-specific paper IDs, e.g. ['2401.00001', '2401.00002']",
        examples=[["2401.00001", "2401.00002"]],
    )


class SubmitPaperResult(BaseModel):
    """Result for a single submitted paper."""

    source_id: str
    status: str  # "queued", "duplicate", "not_found", "error"
    paper_id: int | None = None  # DB id if already exists or newly created
    message: str


class SubmitPaperResponse(BaseModel):
    """Response for the bulk submit endpoint."""

    total: int
    results: list[SubmitPaperResult]
