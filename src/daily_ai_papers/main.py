"""FastAPI application entry point."""

from fastapi import FastAPI

from daily_ai_papers.api import chat, papers, tasks

app = FastAPI(
    title="daily-ai-papers",
    description="Crawl, analyze, translate, display and chat with newest AI papers",
    version="0.1.0",
)

app.include_router(papers.router, prefix="/api/v1/papers", tags=["papers"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
