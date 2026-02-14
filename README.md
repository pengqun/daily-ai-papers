# daily-ai-papers

[![CI](https://github.com/pengqun/daily-ai-papers/actions/workflows/ci.yml/badge.svg)](https://github.com/pengqun/daily-ai-papers/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB.svg)](https://www.python.org/downloads/)

An all-in-one platform for discovering, analyzing, translating, and chatting with the latest AI research papers. Automatically crawls papers from arXiv, analyzes them with LLMs, translates content into multiple languages, and exposes everything via a REST API with a React frontend.

## Features

- **Automated Paper Crawling** -- Daily fetching of new AI papers from arXiv (more sources planned)
- **LLM-Powered Analysis** -- Extracts summaries, key contributions, methodology, and keywords using OpenAI / Anthropic models
- **PDF Parsing** -- Full-text extraction from paper PDFs via PyMuPDF
- **Multi-Language Translation** -- Translates titles, abstracts, and summaries into Chinese, Japanese, Spanish, and more
- **REST API** -- FastAPI endpoints for listing, searching, and submitting papers
- **Background Processing** -- Celery + Redis task queue for crawling, parsing, and translation pipelines
- **React Frontend** -- TypeScript + Vite SPA for browsing and interacting with papers

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                   React Frontend (Vite)                   │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│                  API Gateway (FastAPI)                     │
│              /api/v1/papers, /api/v1/chat ...              │
└───────┬──────────────┬───────────────┬───────────────────┘
        │              │               │
  ┌─────▼─────┐  ┌─────▼──────┐  ┌────▼──────┐
  │  Crawler   │  │  Parser /  │  │   Chat    │
  │  Service   │  │  Analyzer  │  │  Service  │
  └─────┬─────┘  └─────┬──────┘  └────┬──────┘
        │              │               │
  ┌─────▼──────────────▼───────────────▼───────┐
  │            Celery Task Queue                │
  │              (Redis Broker)                 │
  └─────┬──────────────┬───────────────┬───────┘
        │              │               │
  ┌─────▼──────────────▼───────────────▼───────┐
  │          PostgreSQL + pgvector              │
  │    papers | authors | embeddings | tags     │
  └────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| Backend | FastAPI, SQLAlchemy 2.0 (async), Pydantic v2 |
| Frontend | React, TypeScript, Vite |
| Database | PostgreSQL 17 + pgvector |
| Task Queue | Celery + Redis |
| PDF Processing | PyMuPDF |
| LLM | OpenAI / Anthropic SDK (+ Groq, OpenRouter, Gemini via compatible APIs) |
| Linting | Ruff, MyPy (strict) |
| CI | GitHub Actions |
| Containerization | Docker + Docker Compose |

## Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 20+** (for frontend)
- **Docker & Docker Compose** (recommended) or local PostgreSQL + Redis

### Quick Start with Docker

```bash
# Clone the repository
git clone https://github.com/pengqun/daily-ai-papers.git
cd daily-ai-papers

# Configure environment
cp .env.example .env
# Edit .env to add your LLM API key (see Configuration below)

# Start all services
cd docker && docker-compose up -d
```

The API is available at `http://localhost:8000` and auto-generated docs at `http://localhost:8000/docs`.

### Local Development Setup

```bash
# Install Python dependencies
pip install -e ".[dev]"

# Install frontend dependencies
cd frontend && npm install && cd ..

# Start PostgreSQL and Redis (via Docker or locally)
cd docker && docker-compose up -d postgres redis && cd ..

# Configure environment
cp .env.example .env

# Run the API server
uvicorn daily_ai_papers.main:app --reload --port 8000

# Run the frontend dev server (in another terminal)
cd frontend && npm run dev
```

## Configuration

All configuration is done via environment variables. Copy `.env.example` to `.env` and edit as needed.

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL async connection string | `postgresql+asyncpg://postgres:postgres@localhost:5432/daily_ai_papers` |
| `REDIS_URL` | Redis broker URL | `redis://localhost:6379/0` |
| `LLM_PROVIDER` | LLM backend: `openai`, `anthropic`, or `fake` | `openai` |
| `LLM_API_KEY` | API key for the chosen provider | -- |
| `LLM_BASE_URL` | Override for OpenAI-compatible APIs (Groq, OpenRouter, Gemini, etc.) | -- |
| `LLM_MODEL` | Model name | `gpt-4o-mini` |
| `CRAWL_CATEGORIES` | arXiv categories to crawl | `cs.AI,cs.CL,cs.CV,cs.LG,stat.ML` |
| `TRANSLATION_LANGUAGES` | Target translation languages | `zh,ja,es` |

<details>
<summary>Free LLM provider examples</summary>

```bash
# Groq (console.groq.com)
LLM_API_KEY=gsk_...
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile

# OpenRouter (openrouter.ai)
LLM_API_KEY=sk-or-...
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=deepseek/deepseek-r1:free

# Google AI Studio / Gemini (aistudio.google.com)
LLM_API_KEY=AIza...
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_MODEL=gemini-2.0-flash

# Cerebras (cloud.cerebras.ai)
LLM_API_KEY=csk-...
LLM_BASE_URL=https://api.cerebras.ai/v1
LLM_MODEL=llama-3.3-70b
```

</details>

## API Usage

### List papers

```bash
curl http://localhost:8000/api/v1/papers
```

### Get paper details

```bash
curl http://localhost:8000/api/v1/papers/1
```

### Submit papers for crawling

```bash
curl -X POST http://localhost:8000/api/v1/papers/submit \
  -H "Content-Type: application/json" \
  -d '{"source": "arxiv", "paper_ids": ["1706.03762"]}'
```

### Trigger a manual crawl

```bash
curl -X POST http://localhost:8000/api/v1/tasks/crawl
```

Full interactive API docs are available at `/docs` (Swagger UI) or `/redoc` when the server is running.

## Project Structure

```
daily-ai-papers/
├── src/daily_ai_papers/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Pydantic-settings configuration
│   ├── database.py          # SQLAlchemy async engine & session
│   ├── models/              # ORM models (Paper, Author)
│   ├── schemas/             # Pydantic request/response schemas
│   ├── api/                 # FastAPI route handlers
│   ├── services/
│   │   ├── crawler/         # Paper crawlers (arXiv, etc.)
│   │   ├── parser/          # PDF extraction & LLM analysis
│   │   ├── llm_client.py    # Unified LLM client
│   │   ├── translator.py    # Multi-language translation
│   │   └── submission.py    # Manual paper submission
│   └── tasks/               # Celery task definitions
├── frontend/                # React + TypeScript + Vite SPA
├── tests/                   # pytest test suite
├── docker/                  # Dockerfile & docker-compose.yml
├── docs/                    # Architecture documentation
└── pyproject.toml           # Project metadata & dependencies
```

## Development

### Running Tests

```bash
# All tests
pytest

# Offline tests only (no DB or network needed)
pytest tests/test_fake_llm.py -v

# With coverage
pytest --cov=daily_ai_papers tests/
```

### Linting & Formatting

```bash
# Lint check
ruff check src tests

# Auto-fix lint errors
ruff check --fix src tests

# Format code
ruff format src tests

# Type checking
mypy src/
```

### Docker Services

| Service | Description | Port |
|---------|-------------|------|
| `api` | FastAPI application (hot-reload) | 8000 |
| `worker` | Celery worker for async tasks | -- |
| `beat` | Celery Beat scheduler (daily crawl) | -- |
| `postgres` | PostgreSQL 17 + pgvector | 5432 |
| `redis` | Redis 7 (Celery broker) | 6379 |

## Roadmap

| Phase | Status | Scope |
|-------|--------|-------|
| 1 -- Foundation | Done | Project setup, models, config, basic API |
| 2 -- Crawlers | Partial | arXiv crawler works; Semantic Scholar & scheduled task pending |
| 3 -- Parser & Analyzer | Partial | PDF parsing & LLM analysis services done; Celery pipeline pending |
| 4 -- Search & Embeddings | Planned | pgvector semantic search, text chunking, hybrid search API |
| 5 -- Translation | Partial | Translation service done; pipeline integration pending |
| 6 -- Chat (RAG) | Planned | RAG pipeline, chat API, conversation history |
| 7 -- User Features | Planned | Daily digest, bookmarks, tags, notifications |

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full system design document.

## Contributing

Contributions are welcome! Here's how to get started:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes and ensure tests pass (`pytest`)
4. Run linting (`ruff check src tests && mypy src/`)
5. Commit your changes (`git commit -m "Add your feature"`)
6. Push to the branch (`git push origin feature/your-feature`)
7. Open a Pull Request

Please make sure your code follows the existing style conventions (Ruff + MyPy strict) and includes tests for new functionality.

## License

This project is licensed under the [Apache License 2.0](LICENSE).
