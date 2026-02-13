"""Paper-related Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel


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
