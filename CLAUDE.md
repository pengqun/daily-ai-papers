# CLAUDE.md

This file provides guidance for AI assistants working with the **daily-ai-papers** codebase.

## Project Overview

An all-in-one platform for discovering, analyzing, translating, and chatting with the latest AI research papers. It crawls papers from arXiv (and future sources), analyzes them with LLMs, translates content into multiple languages, and exposes everything via a FastAPI REST API.

**Stack:** Python 3.11+ | FastAPI | SQLAlchemy 2.0 (async) | PostgreSQL + pgvector | Celery + Redis | PyMuPDF | OpenAI/Anthropic SDKs

## Repository Structure

```
src/daily_ai_papers/
├── main.py                  # FastAPI app entry point, router registration
├── config.py                # Pydantic-settings config (reads .env)
├── database.py              # SQLAlchemy async engine & session factory
├── models/
│   └── paper.py             # ORM models: Paper, Author, PaperAuthor
├── schemas/
│   ├── paper.py             # Pydantic request/response schemas for papers
│   └── chat.py              # Pydantic schemas for chat endpoint
├── api/
│   ├── papers.py            # GET/POST paper endpoints (implemented)
│   ├── chat.py              # Chat endpoint (stub)
│   └── tasks.py             # Task management endpoints (implemented)
├── services/
│   ├── crawler/
│   │   ├── base.py          # Abstract BaseCrawler interface + CrawledPaper dataclass
│   │   └── arxiv.py         # ArxivCrawler using feedparser (OAI-PMH Atom feeds)
│   ├── parser/
│   │   ├── pdf_extractor.py # PDF download (httpx) + text extraction (PyMuPDF)
│   │   └── metadata_extractor.py  # LLM-based structured metadata extraction
│   ├── llm_client.py        # Unified LLM client (OpenAI/Anthropic/fake providers)
│   ├── submission.py        # Manual paper submission workflow
│   └── translator.py        # LLM-based multi-language translation
└── tasks/
    ├── celery_app.py        # Celery config, Redis broker, Beat scheduling
    ├── crawl_tasks.py       # Crawling Celery tasks
    └── parse_tasks.py       # Parsing Celery tasks

tests/
├── conftest.py              # Shared fixtures (api_client)
├── test_api_integration.py  # FastAPI endpoint tests
├── test_crawler_integration.py  # arXiv API integration tests
├── test_fake_llm.py         # LLM tests using fake provider (no API key needed)
├── test_llm_integration.py  # Real LLM provider tests
├── test_pdf_extractor_integration.py  # PDF extraction tests
├── test_pipeline_e2e.py     # End-to-end pipeline tests
└── test_tasks_api.py        # Task API endpoint tests

docker/
├── Dockerfile               # python:3.11-slim + libmupdf-dev
└── docker-compose.yml       # 5 services: api, worker, beat, postgres (pgvector), redis

docs/
└── ARCHITECTURE.md          # Detailed system design document
```

## Development Commands

### Install

```bash
pip install -e ".[dev]"
```

### Run Tests

```bash
# All tests (some require network access for arXiv API)
pytest

# Specific test file
pytest tests/test_api_integration.py -v

# Tests that work offline (fake LLM, no DB needed)
pytest tests/test_fake_llm.py -v

# With coverage
pytest --cov=daily_ai_papers tests/
```

### Lint & Format

```bash
# Check lint errors
ruff check src tests

# Auto-fix lint errors
ruff check --fix src tests

# Format code
ruff format src tests

# Type checking
mypy src/
```

### Run the Application

```bash
# Copy and configure environment
cp .env.example .env

# Start with Docker (all services)
cd docker && docker-compose up -d

# Or run API locally (requires postgres + redis running)
uvicorn daily_ai_papers.main:app --reload --port 8000
```

## Key Conventions

### Code Style

- **Line length:** 100 characters
- **Ruff rules:** E, F, I (isort), N (naming), W, UP (pyupgrade), B (bugbear), SIM
- **MyPy:** strict mode with Pydantic plugin
- **Async-first:** all I/O uses async/await (httpx, asyncpg, SQLAlchemy async sessions)

### Naming

- Classes: `PascalCase` (e.g., `BaseCrawler`, `PaperDetail`)
- Functions/methods: `snake_case` (e.g., `fetch_recent_papers`, `extract_text_from_pdf`)
- Constants: `UPPER_CASE` (e.g., `ARXIV_API_URL`, `SYSTEM_PROMPT`)
- Private: `_snake_case` (e.g., `_parse_entry`, `_get_crawler`)

### Architecture Patterns

- **Configuration:** `pydantic-settings` reading from `.env` files
- **Database:** async SQLAlchemy with `asyncpg` driver; Alembic for migrations
- **API layers:** FastAPI routers in `api/` → services in `services/` → ORM models in `models/`
- **Background tasks:** Celery tasks in `tasks/` with Redis broker and Beat scheduler
- **LLM abstraction:** unified client in `llm_client.py` supporting OpenAI, Anthropic, and a `fake` provider for testing
- **Logging:** `logging.getLogger(__name__)` in every module

### Paper Processing Pipeline Status Flow

```
PENDING → CRAWLED → DOWNLOADING → PARSED → ANALYZED → EMBEDDED → READY
```

### Testing

- `pytest-asyncio` with `asyncio_mode = "auto"` — no `@pytest.mark.asyncio` needed
- Known test paper: arXiv ID `1706.03762` (Attention Is All You Need)
- Use `LLM_PROVIDER=fake` for tests that don't need real LLM API calls
- `api_client` fixture provides an `httpx.AsyncClient` wired to the FastAPI test app

## Environment Variables

Key settings (see `.env.example` for full list):

| Variable | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL async connection string | `postgresql+asyncpg://postgres:postgres@localhost:5432/daily_ai_papers` |
| `REDIS_URL` | Redis broker URL | `redis://localhost:6379/0` |
| `LLM_PROVIDER` | `openai`, `anthropic`, or `fake` | `openai` |
| `LLM_API_KEY` | API key for chosen LLM provider | — |
| `LLM_BASE_URL` | Override for OpenAI-compatible APIs (Groq, OpenRouter, etc.) | — |
| `LLM_MODEL` | Model name | `gpt-4o-mini` |
| `CRAWL_CATEGORIES` | Comma-separated arXiv categories | `cs.AI,cs.CL,cs.CV,cs.LG,stat.ML` |
| `TRANSLATION_LANGUAGES` | Target languages for translation | `zh,ja,es` |

## Implementation Status

| Phase | Status | Scope |
|-------|--------|-------|
| 1 | Done | Project setup, models, config, basic API |
| 2 | Partial | Crawler scheduling (arXiv crawler works; `crawl_all_sources` task is a stub) |
| 3 | Partial | PDF parsing + LLM analysis pipeline (services done; Celery task `parse_paper` is a stub) |
| 4 | TODO | Text embeddings + pgvector semantic search |
| 5 | Partial | Multi-language translation pipeline (translator service done; not yet integrated into pipeline) |
| 6 | TODO | Chat/RAG service |
| 7 | TODO | Daily digest, bookmarks, tags, notifications |

## Docker Services

The `docker/docker-compose.yml` orchestrates five services:

1. **api** — FastAPI on port 8000 (hot-reload via volume mount)
2. **worker** — Celery worker for async task execution
3. **beat** — Celery Beat for periodic scheduling (daily crawl)
4. **postgres** — PostgreSQL 17 with pgvector extension (port 5432)
5. **redis** — Redis 7 as Celery broker (port 6379)
