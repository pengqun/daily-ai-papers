# daily-ai-papers: Service Architecture Plan

## 1. Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Language | Python 3.11+ | AI/ML ecosystem, arXiv API libraries, PDF processing |
| Web Framework | FastAPI | Async support, auto-generated OpenAPI docs, high performance |
| Task Queue | Celery + Redis | Reliable async task scheduling for crawling & parsing |
| Database | PostgreSQL | Robust relational storage, JSON support, mature ecosystem |
| Vector Store | pgvector (PostgreSQL extension) | Paper embeddings for semantic search & chat, no extra infra |
| ORM | SQLAlchemy 2.0 + Alembic | Type-safe queries, schema migrations |
| PDF Processing | PyMuPDF (fitz) | Fast full-text extraction from paper PDFs |
| LLM Integration | OpenAI / Anthropic API | Paper analysis, translation, chat |
| Containerization | Docker + Docker Compose | Consistent dev/prod environments |
| Testing | pytest + pytest-asyncio | Standard Python testing with async support |
| Linting | Ruff | Fast all-in-one linter and formatter |

## Implementation Status

This document serves as both architectural specification and implementation blueprint. Items are annotated with their current status:

- **[DONE]** — Fully implemented and tested
- **[PARTIAL]** — Component exists but not fully wired into the pipeline
- **[PLANNED]** — Design specification, not yet implemented

> **Current state:** Only `pending` and `crawled` paper statuses are used in practice. Phases 1–3 and 5 are partially complete; Phases 4, 6, 7 are planned.

## 2. Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway (FastAPI)                   │
│                   /api/v1/papers, /api/v1/chat ...          │
└────────┬──────────────┬───────────────┬─────────────────────┘
         │              │               │
   ┌─────▼─────┐ ┌─────▼──────┐ ┌─────▼──────┐
   │  Crawler   │ │  Parser /  │ │   Chat     │
   │  Service   │ │  Analyzer  │ │  Service   │
   └─────┬─────┘ └─────┬──────┘ └─────┬──────┘
         │              │               │
   ┌─────▼──────────────▼───────────────▼─────┐
   │            Celery Task Queue              │
   │              (Redis Broker)               │
   └─────┬──────────────┬───────────────┬─────┘
         │              │               │
   ┌─────▼──────────────▼───────────────▼─────┐
   │         PostgreSQL + pgvector             │
   │   papers | authors | embeddings | tags    │
   └──────────────────────────────────────────┘
```

### Service Descriptions

| Service | Responsibility |
|---------|---------------|
| **API Gateway** | Unified REST API entry point, authentication, rate limiting |
| **Crawler Service** | Scheduled paper fetching from arXiv, Semantic Scholar, etc. |
| **Parser / Analyzer** | PDF download, full-text extraction, LLM-based metadata extraction |
| **Chat Service** | RAG-based Q&A over paper content using vector search |
| **Celery Workers** | Execute async tasks (crawl, parse, translate, embed) |

## 3. Project Directory Structure

### Current Structure (implemented)

```
daily-ai-papers/
├── src/
│   └── daily_ai_papers/
│       ├── __init__.py
│       ├── main.py                 # FastAPI app entry point
│       ├── config.py               # Settings via pydantic-settings
│       ├── database.py             # SQLAlchemy engine & session
│       │
│       ├── models/                 # SQLAlchemy ORM models
│       │   ├── __init__.py
│       │   └── paper.py            # Paper, Author, PaperAuthor
│       │
│       ├── schemas/                # Pydantic request/response schemas
│       │   ├── __init__.py
│       │   ├── paper.py
│       │   └── chat.py
│       │
│       ├── api/                    # FastAPI routers
│       │   ├── __init__.py
│       │   ├── papers.py           # CRUD endpoints (list, detail, submit)
│       │   ├── chat.py             # Chat endpoint (stub)
│       │   └── tasks.py            # Task management endpoints
│       │
│       ├── services/               # Business logic layer
│       │   ├── __init__.py
│       │   ├── crawler/
│       │   │   ├── __init__.py
│       │   │   ├── base.py         # Abstract crawler interface
│       │   │   └── arxiv.py        # arXiv crawler implementation
│       │   ├── parser/
│       │   │   ├── __init__.py
│       │   │   ├── pdf_extractor.py    # PDF to text
│       │   │   └── metadata_extractor.py # LLM-based metadata extraction
│       │   ├── llm_client.py       # Unified LLM client (OpenAI/Anthropic/fake)
│       │   ├── submission.py       # Manual paper submission workflow
│       │   └── translator.py       # LLM-based translation
│       │
│       └── tasks/                  # Celery task definitions
│           ├── __init__.py
│           ├── celery_app.py       # Celery configuration
│           ├── crawl_tasks.py      # Periodic crawl tasks
│           └── parse_tasks.py      # Parse & embed tasks (stub)
│
├── frontend/                       # React + TypeScript + Vite SPA
│   ├── src/
│   └── ...
│
├── tests/
│   ├── conftest.py
│   ├── test_api_integration.py
│   ├── test_crawler_integration.py
│   ├── test_fake_llm.py
│   ├── test_llm_integration.py
│   ├── test_pdf_extractor_integration.py
│   ├── test_pipeline_e2e.py
│   └── test_tasks_api.py
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── pyproject.toml                  # Project metadata & dependencies
├── .env.example                    # Environment variable template
└── README.md
```

### Planned Additions

```
src/daily_ai_papers/
├── models/
│   ├── tag.py              # [Phase 7] Tag, PaperTag
│   └── embedding.py        # [Phase 4] PaperEmbedding (pgvector)
├── services/
│   ├── crawler/
│   │   └── semantic_scholar.py  # [Phase 2] Semantic Scholar crawler
│   ├── embedding.py        # [Phase 4] Text embedding generation
│   └── chat.py             # [Phase 6] RAG chat logic
│
migrations/                 # Alembic migrations (to be initialized)
│   ├── env.py
│   └── versions/
alembic.ini                 # Alembic config
scripts/
│   └── seed_data.py        # Development seed script
```

## 4. Data Models

### 4.1 Core Tables

```
┌──────────────────────┐       ┌──────────────────┐
│   papers [DONE]      │       │  authors [DONE]  │
├──────────────────────┤       ├──────────────────┤
│ id (PK)              │       │ id (PK)          │
│ source               │       │ name             │
│ source_id            │  M:N  │ affiliation      │
│ title                │◄─────►│ created_at       │
│ abstract             │       └──────────────────┘
│ pdf_url              │
│ published_at         │       ┌──────────────────────┐
│ categories           │       │ paper_authors [DONE] │
│ full_text            │       ├──────────────────────┤
│ summary              │       │ paper_id (FK)        │
│ summary_zh           │       │ author_id (FK)       │
│ contributions        │       │ position             │
│ methodology          │       └──────────────────────┘
│ results              │
│ keywords (ARRAY)     │       ┌──────────────────────────┐
│ status               │       │    tags [PLANNED Ph.7]   │
│ created_at           │       ├──────────────────────────┤
│ updated_at           │       │ id (PK)                  │
└──────┬───────────────┘       │ name (UNIQUE)            │
       │                 M:N   │ created_at               │
       │◄─────────────────────►└──────────────────────────┘
       │
       │ 1:N     ┌───────────────────────────────────┐
       └────────►│  paper_embeddings [PLANNED Ph.4]  │
                 ├───────────────────────────────────┤
                 │ id (PK)                           │
                 │ paper_id (FK)                     │
                 │ chunk_index                       │
                 │ chunk_text                        │
                 │ embedding (vector)                │
                 └───────────────────────────────────┘
```

### 4.2 Paper Status Flow

```
PENDING → CRAWLED → DOWNLOADING → PARSED → ANALYZED → EMBEDDED → READY
                                                         │
                                                    (translation)
                                                         │
                                                      TRANSLATED
```

| Status | Description |
|--------|-------------|
| `pending` | Source URL known, not yet fetched |
| `crawled` | Metadata fetched from source API |
| `downloading` | PDF is being downloaded |
| `parsed` | Full text extracted from PDF |
| `analyzed` | LLM extracted summary, contributions, keywords |
| `embedded` | Text chunks embedded into vector store |
| `ready` | Fully processed and available for search/chat |
| `failed` | Processing failed at some stage |

> **Note:** Currently only `pending` and `crawled` statuses are used. The remaining statuses will be activated as the Celery pipeline tasks are implemented.

## 5. API Design

### 5.1 Paper Endpoints

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| GET | `/api/v1/papers` | List papers (paginated, filterable) | [DONE] |
| GET | `/api/v1/papers/{id}` | Get paper detail | [DONE] |
| POST | `/api/v1/papers/submit` | Manually submit paper IDs to crawl (see below) | [DONE] |
| GET | `/api/v1/papers/search` | Full-text + semantic search | [PLANNED Ph.4] |
| POST | `/api/v1/papers/{id}/bookmark` | Bookmark a paper | [PLANNED Ph.7] |
| POST | `/api/v1/papers/{id}/tags` | Add tags to a paper | [PLANNED Ph.7] |
| GET | `/api/v1/papers/daily-digest` | Get today's digest | [PLANNED Ph.7] |

### 5.2 Chat Endpoints

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| POST | `/api/v1/chat` | Ask a question about one or more papers | [PLANNED Ph.6] (stub exists) |
| GET | `/api/v1/chat/history` | Get chat history | [PLANNED Ph.6] |

### 5.3 Task / Admin Endpoints

| Method | Path | Description | Status |
|--------|------|-------------|--------|
| POST | `/api/v1/tasks/crawl` | Trigger a manual crawl | [DONE] |
| GET | `/api/v1/tasks/{task_id}` | Get task status | [DONE] |

### 5.4 Paper Submission (Manual Crawl)

Users can proactively submit papers by providing source-specific IDs (e.g. arXiv IDs).

**Request:** `POST /api/v1/papers/submit`

```json
{
  "source": "arxiv",
  "paper_ids": ["2401.00001", "2401.00002"]
}
```

**Response:**

```json
{
  "total": 2,
  "results": [
    {
      "source_id": "2401.00001",
      "status": "queued",
      "paper_id": 42,
      "message": "Paper queued for processing: Attention Is All You Need"
    },
    {
      "source_id": "2401.00002",
      "status": "duplicate",
      "paper_id": 17,
      "message": "Paper already exists (id=17)"
    }
  ]
}
```

**Result statuses:**

| Status | Meaning |
|--------|---------|
| `queued` | New paper created and queued for parsing |
| `duplicate` | Paper already exists in the database |
| `not_found` | Source API returned no result for this ID |
| `error` | Unexpected failure fetching this ID |

**Flow:**

```
User submits IDs via API
        │
        ▼
 ┌──────────────┐    per ID     ┌──────────────────┐
 │ Submit API   │──────────────►│ Crawler           │
 │ endpoint     │               │ .fetch_paper_by_id│
 └──────┬───────┘               └────────┬─────────┘
        │                                │
        ▼                                ▼
 ┌──────────────┐               ┌──────────────────┐
 │ Dedup check  │               │ Return metadata   │
 │ (DB lookup)  │               │ or None           │
 └──────┬───────┘               └──────────────────┘
        │
        ▼
 ┌──────────────┐    async      ┌──────────────────┐
 │ Store paper  │──────────────►│ Parse task        │
 │ status=crawled│              │ (Celery)          │
 └──────────────┘               └──────────────────┘
```

## 6. Crawler Design

### 6.1 Abstract Interface

```python
class BaseCrawler(ABC):
    @abstractmethod
    async def fetch_recent_papers(
        self,
        categories: list[str],
        max_results: int,
        days_back: int,
    ) -> list[CrawledPaper]: ...

    @abstractmethod
    async def fetch_paper_by_id(self, paper_id: str) -> CrawledPaper | None:
        """Fetch a single paper by source-specific ID (used by manual submission)."""
        ...
```

### 6.2 Data Sources

| Source | API | Rate Limit | Categories | Status |
|--------|-----|-----------|------------|--------|
| arXiv | OAI-PMH / Atom Feed | 1 req/3s | cs.AI, cs.CL, cs.CV, cs.LG, stat.ML | [DONE] |
| Semantic Scholar | REST API | 100 req/5min (free) | AI/ML filtered by field of study | [PLANNED Ph.2] |

### 6.3 Scheduling

- **Celery Beat** runs a periodic crawl task daily at configurable time (default: 06:00 UTC)
- Each crawl creates individual parse tasks per paper (fan-out pattern)
- Deduplication by `(source, source_id)` unique constraint

## 7. Parser / Analyzer Pipeline

```
PDF URL
  │
  ▼
┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ PDF Download │───►│ Text Extraction  │───►│ LLM Analysis    │
│ (httpx)      │    │ (PyMuPDF)        │    │ (structured     │
│              │    │                  │    │  output)        │
└─────────────┘    └──────────────────┘    └────────┬────────┘
                                                     │
                        ┌────────────────────────────┤
                        │                            │
                        ▼                            ▼
               ┌────────────────┐          ┌─────────────────┐
               │ Translation    │          │ Chunk & Embed   │
               │ (LLM)         │          │ (text-embedding) │
               └────────────────┘          └─────────────────┘
```

### LLM Analysis Output (structured)

```json
{
  "summary": "A concise 3-5 sentence summary...",
  "contributions": ["Contribution 1", "Contribution 2"],
  "keywords": ["keyword1", "keyword2"],
  "methodology": "Brief description of the approach",
  "results": "Key findings"
}
```

## 8. Chat Service (RAG)

1. User asks a question about a paper (or across papers)
2. Question is embedded using the same embedding model
3. pgvector similarity search retrieves top-K relevant chunks
4. Chunks + question are sent to LLM as context
5. LLM generates an answer grounded in the paper text

## 9. Implementation Phases

### Phase 1: Foundation (Core Infrastructure) — DONE
- [x] Project scaffolding: `pyproject.toml`, directory structure, Docker setup
- [x] Database models (Alembic not yet initialized)
- [x] Configuration management (`pydantic-settings`)
- [x] Basic FastAPI app with health check

### Phase 2: Crawler Service — PARTIAL
- [x] arXiv crawler implementation (OAI-PMH / Atom feed)
- [ ] Semantic Scholar crawler
- [ ] Celery task for scheduled crawling (`crawl_all_sources` is a stub)
- [x] Paper list API endpoints (GET /papers, GET /papers/{id})
- [x] Paper submission API (POST /papers/submit)

### Phase 3: Parser & Analyzer — PARTIAL
- [x] PDF download service (`pdf_extractor.py`)
- [x] Full-text extraction (PyMuPDF)
- [x] LLM-based metadata extraction (summary, contributions, keywords)
- [ ] Celery task pipeline: download → parse → analyze (`parse_paper` is a stub)

### Phase 4: Search & Embeddings — TODO
- [ ] Text chunking strategy
- [ ] Embedding generation (OpenAI / open-source model)
- [ ] pgvector storage and similarity search
- [ ] Search API endpoint (full-text + semantic hybrid)

### Phase 5: Translation — PARTIAL
- [x] LLM-based translation service (title, abstract, summary)
- [x] Support for Chinese, Japanese, Spanish (+ French, German, Korean)
- [ ] Async translation task in pipeline

### Phase 6: Chat — TODO
- [ ] RAG pipeline: embed question → retrieve chunks → generate answer
- [ ] Chat API endpoint (stub exists)
- [ ] Chat history storage

### Phase 7: Notifications & User Features — TODO
- [ ] Daily digest generation
- [ ] Bookmarking & tagging
- [ ] Email notification (optional)

## 10. Configuration

All configuration via environment variables with defaults:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/daily_ai_papers

# Redis
REDIS_URL=redis://localhost:6379/0

# LLM
LLM_PROVIDER=openai          # or "anthropic" or "fake" (for testing)
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini        # for analysis & chat
EMBEDDING_MODEL=text-embedding-3-small

# Crawler
CRAWL_SCHEDULE_HOUR=6         # UTC hour for daily crawl
CRAWL_CATEGORIES=cs.AI,cs.CL,cs.CV,cs.LG,stat.ML
CRAWL_MAX_RESULTS=100
CRAWL_DAYS_BACK=1

# Translation
TRANSLATION_LANGUAGES=zh,ja,es
```

## 11. Docker Compose Services

```yaml
services:
  api:        # FastAPI application
  worker:     # Celery worker
  beat:       # Celery beat scheduler
  postgres:   # PostgreSQL + pgvector
  redis:      # Redis (Celery broker + cache)
```

## 12. Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Monorepo vs Microservice | Monorepo with modular services | Simpler deployment and shared models; split later if needed |
| Sync vs Async | Async (asyncpg, httpx) | Non-blocking I/O for crawling and API serving |
| Vector DB | pgvector over dedicated vector DB | Avoid extra infrastructure; good enough for < 1M papers |
| PDF parsing | PyMuPDF over cloud OCR | Free, fast, works well for arXiv papers (born-digital) |
| Task queue | Celery over custom | Battle-tested, periodic scheduling built-in |
| LLM structured output | Pydantic model with function calling | Type-safe, validated extraction results |
