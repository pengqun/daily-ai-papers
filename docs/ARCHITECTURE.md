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
│       │   ├── paper.py            # Paper, Author, PaperAuthor
│       │   ├── tag.py              # Tag, PaperTag
│       │   └── embedding.py        # PaperEmbedding (pgvector)
│       │
│       ├── schemas/                # Pydantic request/response schemas
│       │   ├── __init__.py
│       │   ├── paper.py
│       │   └── chat.py
│       │
│       ├── api/                    # FastAPI routers
│       │   ├── __init__.py
│       │   ├── papers.py           # CRUD + search endpoints
│       │   ├── chat.py             # Chat endpoints
│       │   └── tasks.py            # Task status endpoints
│       │
│       ├── services/               # Business logic layer
│       │   ├── __init__.py
│       │   ├── crawler/
│       │   │   ├── __init__.py
│       │   │   ├── base.py         # Abstract crawler interface
│       │   │   ├── arxiv.py        # arXiv crawler implementation
│       │   │   └── semantic_scholar.py
│       │   ├── parser/
│       │   │   ├── __init__.py
│       │   │   ├── pdf_extractor.py    # PDF to text
│       │   │   └── metadata_extractor.py # LLM-based metadata extraction
│       │   ├── translator.py       # LLM-based translation
│       │   ├── embedding.py        # Text embedding generation
│       │   └── chat.py             # RAG chat logic
│       │
│       └── tasks/                  # Celery task definitions
│           ├── __init__.py
│           ├── celery_app.py       # Celery configuration
│           ├── crawl_tasks.py      # Periodic crawl tasks
│           └── parse_tasks.py      # Parse & embed tasks
│
├── migrations/                     # Alembic migrations
│   ├── env.py
│   └── versions/
│
├── tests/
│   ├── conftest.py
│   ├── test_crawler/
│   ├── test_parser/
│   └── test_api/
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── scripts/
│   └── seed_data.py                # Development seed script
│
├── pyproject.toml                  # Project metadata & dependencies
├── alembic.ini                     # Alembic config
├── .env.example                    # Environment variable template
└── README.md
```

## 4. Data Models

### 4.1 Core Tables

```
┌──────────────────┐       ┌──────────────────┐
│     papers       │       │     authors      │
├──────────────────┤       ├──────────────────┤
│ id (PK)          │       │ id (PK)          │
│ source           │       │ name             │
│ source_id        │  M:N  │ affiliation      │
│ title            │◄─────►│ created_at       │
│ abstract         │       └──────────────────┘
│ pdf_url          │
│ published_at     │       ┌──────────────────┐
│ categories       │       │  paper_authors   │
│ full_text        │       ├──────────────────┤
│ summary          │       │ paper_id (FK)    │
│ summary_zh       │       │ author_id (FK)   │
│ contributions    │       │ position         │
│ keywords (ARRAY) │       └──────────────────┘
│ status           │
│ created_at       │       ┌──────────────────┐
│ updated_at       │       │      tags        │
└──────┬───────────┘       ├──────────────────┤
       │                   │ id (PK)          │
       │             M:N   │ name (UNIQUE)    │
       │◄─────────────────►│ created_at       │
       │                   └──────────────────┘
       │
       │ 1:N         ┌──────────────────────┐
       └────────────►│  paper_embeddings    │
                     ├──────────────────────┤
                     │ id (PK)              │
                     │ paper_id (FK)        │
                     │ chunk_index          │
                     │ chunk_text           │
                     │ embedding (vector)   │
                     └──────────────────────┘
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

## 5. API Design

### 5.1 Paper Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/papers` | List papers (paginated, filterable) |
| GET | `/api/v1/papers/{id}` | Get paper detail |
| GET | `/api/v1/papers/search` | Full-text + semantic search |
| POST | `/api/v1/papers/{id}/bookmark` | Bookmark a paper |
| POST | `/api/v1/papers/{id}/tags` | Add tags to a paper |
| GET | `/api/v1/papers/daily-digest` | Get today's digest |

### 5.2 Chat Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/chat` | Ask a question about one or more papers |
| GET | `/api/v1/chat/history` | Get chat history |

### 5.3 Task / Admin Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/tasks/crawl` | Trigger a manual crawl |
| GET | `/api/v1/tasks/{task_id}` | Get task status |

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
```

### 6.2 Data Sources

| Source | API | Rate Limit | Categories |
|--------|-----|-----------|------------|
| arXiv | OAI-PMH / Atom Feed | 1 req/3s | cs.AI, cs.CL, cs.CV, cs.LG, stat.ML |
| Semantic Scholar | REST API | 100 req/5min (free) | AI/ML filtered by field of study |

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

### Phase 1: Foundation (Core Infrastructure)
- [ ] Project scaffolding: `pyproject.toml`, directory structure, Docker setup
- [ ] Database models + Alembic migrations
- [ ] Configuration management (`pydantic-settings`)
- [ ] Basic FastAPI app with health check

### Phase 2: Crawler Service
- [ ] arXiv crawler implementation (OAI-PMH / Atom feed)
- [ ] Semantic Scholar crawler
- [ ] Celery task for scheduled crawling
- [ ] Paper list API endpoints (GET /papers, GET /papers/{id})

### Phase 3: Parser & Analyzer
- [ ] PDF download service
- [ ] Full-text extraction (PyMuPDF)
- [ ] LLM-based metadata extraction (summary, contributions, keywords)
- [ ] Celery task pipeline: download → parse → analyze

### Phase 4: Search & Embeddings
- [ ] Text chunking strategy
- [ ] Embedding generation (OpenAI / open-source model)
- [ ] pgvector storage and similarity search
- [ ] Search API endpoint (full-text + semantic hybrid)

### Phase 5: Translation
- [ ] LLM-based translation service (title, abstract, summary)
- [ ] Support for Chinese, Japanese, Spanish (configurable)
- [ ] Async translation task in pipeline

### Phase 6: Chat
- [ ] RAG pipeline: embed question → retrieve chunks → generate answer
- [ ] Chat API endpoint
- [ ] Chat history storage

### Phase 7: Notifications & User Features
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
LLM_PROVIDER=openai          # or "anthropic"
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
