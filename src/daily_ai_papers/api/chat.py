"""Chat API endpoints."""

from fastapi import APIRouter

from daily_ai_papers.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat_with_papers(request: ChatRequest) -> ChatResponse:
    """Ask a question about one or more papers using RAG."""
    # TODO: Implement RAG pipeline in Phase 6
    return ChatResponse(
        answer="Chat service is not yet implemented.",
        source_papers=[],
        source_chunks=[],
    )
