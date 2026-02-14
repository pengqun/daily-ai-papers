# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Platform for discovering, analyzing, translating, and chatting with AI research papers. Crawls from arXiv, analyzes with LLMs, translates to multiple languages, serves via FastAPI + React frontend.

**Backend:** Python 3.11+ | FastAPI | SQLAlchemy 2.0 (async) | PostgreSQL + pgvector | Celery + Redis | PyMuPDF | OpenAI/Anthropic SDKs
**Frontend:** React 19 | TypeScript | Vite | Tailwind CSS 4 | React Router 7

## Development Commands

```bash
# Backend install
pip install -e ".[dev]"

# Frontend install
cd frontend && npm install

# Run all tests (some need network for arXiv API)
pytest

# Run a single test file
pytest tests/test_api_integration.py -v

# Offline tests (no DB, no API keys)
pytest tests/test_fake_llm.py -v

# Lint & format
ruff check src tests          # lint check
ruff check --fix src tests    # auto-fix
ruff format src tests         # format
mypy src/                     # type check (strict mode)

# Frontend lint & build
cd frontend && npm run lint && npm run build

# Start all services via Docker
cd docker && docker-compose up -d

# Run API locally (needs postgres + redis running)
uvicorn daily_ai_papers.main:app --reload --port 8000

# Run frontend dev server
cd frontend && npm run dev
```

## Architecture

### Request Flow

```
React SPA (Vite) → FastAPI routers (api/) → Services (services/) → DB / External APIs
                                           → Celery tasks (tasks/) → Redis broker
```

- **API layer** (`api/papers.py`, `api/tasks.py`, `api/chat.py`): FastAPI routers handle HTTP, delegate to services
- **Services layer** (`services/`): Business logic — crawlers, PDF parsing, LLM calls, translation
- **Models layer** (`models/paper.py`): SQLAlchemy 2.0 async ORM with `Mapped[]` type annotations
- **Tasks layer** (`tasks/`): Celery tasks for background processing; Beat for daily scheduling

### LLM Client (`services/llm_client.py`)

Unified `llm_complete()` function dispatches to OpenAI, Anthropic, or a `fake` provider based on `LLM_PROVIDER` env var. The `fake` provider returns canned responses keyed on prompt content — use it for all tests that don't need real LLM output. Also provides `parse_json_response()` for extracting JSON from LLM output (handles markdown code fences).

### Crawler System (`services/crawler/`)

Abstract `BaseCrawler` interface with `fetch_recent_papers()` and `fetch_paper_by_id()`. Currently only `ArxivCrawler` is implemented. New crawlers extend `BaseCrawler` and return `CrawledPaper` dataclasses.

### Paper Processing Pipeline

```
PENDING → CRAWLED → DOWNLOADING → PARSED → ANALYZED → EMBEDDED → READY
```

Currently only `pending` and `crawled` statuses are active. The download→parse→analyze→embed chain needs Celery task implementations (`crawl_all_sources` and `parse_paper` in `tasks/` are stubs).

### Database

- Async SQLAlchemy with `asyncpg` driver; `get_db()` FastAPI dependency yields sessions
- Core tables: `papers` (with `(source, source_id)` unique constraint), `authors`, `paper_authors` (M:N junction)
- PostgreSQL ARRAY columns for `categories`, `contributions`, `keywords`
- pgvector extension installed but embeddings table not yet created

### Frontend (`frontend/`)

React 19 + TypeScript + Vite SPA with Tailwind CSS 4. Pages: Home, Papers list, Paper detail, Submit, Chat. API client in `src/api/client.ts` talks to FastAPI backend. Uses `react-router` v7 and `lucide-react` icons.

## Code Style

- **Line length:** 100 chars, enforced by Ruff
- **Ruff rules:** E, F, I (isort), N, W, UP, B, SIM (see `pyproject.toml`)
- **MyPy:** strict mode with Pydantic plugin; `celery`, `fitz`, `feedparser` have `ignore_missing_imports`
- **Async-first:** all I/O uses async/await — never use synchronous DB or HTTP calls

## Testing

- `pytest-asyncio` with `asyncio_mode = "auto"` — no `@pytest.mark.asyncio` decorator needed
- `api_client` fixture (`conftest.py`): `httpx.AsyncClient` on `ASGITransport` — no real server needed
- Known test paper: arXiv ID `1706.03762` (Attention Is All You Need)
- CI uses `LLM_PROVIDER=fake` with postgres (pgvector/pgvector:pg17) and redis service containers

## Key Environment Variables

See `.env.example` for the full list. Most important:
- `LLM_PROVIDER`: `openai` | `anthropic` | `fake` (default: `openai`)
- `LLM_API_KEY`: required unless using `fake` provider
- `LLM_BASE_URL`: set for OpenAI-compatible APIs (Groq, OpenRouter, Gemini)
- `DATABASE_URL`: async connection string (`postgresql+asyncpg://...`)

## Implementation Status

| Phase | Status | What's Done / What's Missing |
|-------|--------|------------------------------|
| 1 Foundation | Done | Models, config, basic API, Docker |
| 2 Crawlers | Partial | arXiv crawler works; `crawl_all_sources` Celery task is a stub |
| 3 Parser/Analyzer | Partial | PDF extractor + LLM metadata extraction services done; `parse_paper` Celery task is a stub |
| 4 Embeddings | TODO | pgvector semantic search, text chunking, embedding generation |
| 5 Translation | Partial | Translation service done; not wired into pipeline |
| 6 Chat/RAG | TODO | RAG pipeline, chat API (stub exists) |
| 7 User Features | TODO | Daily digest, bookmarks, tags, notifications |
