"""Chat-related Pydantic schemas."""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    paper_ids: list[int] | None = None  # None means search across all papers


class ChatResponse(BaseModel):
    answer: str
    source_papers: list[int]  # IDs of papers used as context
    source_chunks: list[str]  # Relevant text snippets
