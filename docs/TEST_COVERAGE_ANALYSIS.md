# Test Coverage Analysis

## Current State

**Overall line coverage (offline tests): 70%** (235 of 469 statements missed with all tests; 141 missed with offline+fake-LLM tests)

### Per-Module Coverage

| Module | Coverage | Notes |
|--------|----------|-------|
| `api/tasks.py` | 100% | Fully covered via mocked Celery tests |
| `api/chat.py` | 83% | Only the stub response line (14) is uncovered |
| `api/papers.py` | **53%** | `list_papers`, `get_paper`, successful `submit_paper` all untested |
| `config.py` | 91% | `crawl_category_list` and `translation_language_list` properties untested |
| `services/crawler/arxiv.py` | 60% | `fetch_recent_papers` entirely untested in offline suite; `_parse_datetime`/`_parse_entry` only exercised via integration |
| `services/llm_client.py` | 43% | OpenAI and Anthropic provider paths (lines 44-121) are 0% offline; `parse_json_response` edge cases untested |
| `services/parser/pdf_extractor.py` | 64% | `extract_text_from_pdf` untested (PyMuPDF not installed in CI) |
| `services/submission.py` | **27%** | Core logic (`submit_papers`, `_upsert_paper`, `_get_crawler`) almost entirely untested |
| `tasks/crawl_tasks.py` | **29%** | `fetch_submitted_paper` task logic untested |
| `tasks/parse_tasks.py` | **0%** | Stub, but even the stub return path is never executed |

### Test Inventory (14 offline tests)

| File | Tests | What's Covered |
|------|-------|----------------|
| `test_api_integration.py` | 4 | Health check, OpenAPI schema, submit validation errors |
| `test_fake_llm.py` | 6 | Fake LLM completions, metadata extraction, translation (zh/ja), e2e pipeline (fails without PyMuPDF) |
| `test_tasks_api.py` | 4 | Trigger crawl (mocked), task status polling (pending/success/failure) |

Additional integration tests (require network/API keys): `test_crawler_integration.py` (3), `test_llm_integration.py` (5), `test_pdf_extractor_integration.py` (2), `test_pipeline_e2e.py` (2).

---

## Recommended Improvements

### Priority 1: Unit Tests for Core Business Logic (no DB or network needed)

These are the highest-value additions because they test critical logic paths that currently have 0-27% coverage, and they can run fast with no external dependencies.

#### 1.1 `services/submission.py` — `_get_crawler()` and `_upsert_paper()`
**Current coverage: 27%.** The `_get_crawler` function is a simple registry lookup that should be tested for both known sources (`"arxiv"`) and unknown sources (`ValueError`). The `_upsert_paper` function contains the duplicate-detection logic (check by `source + source_id`) and paper creation — this is the most important untested business logic in the codebase.

**Suggested tests:**
- `_get_crawler("arxiv")` returns `ArxivCrawler`
- `_get_crawler("unknown")` raises `ValueError`
- `_upsert_paper` with a new paper creates a `Paper` and returns `is_new=True`
- `_upsert_paper` with an existing `(source, source_id)` returns the existing paper and `is_new=False`
- `submit_papers` with a mix of valid/invalid/duplicate IDs returns correct statuses

These tests need an in-memory SQLite async session (or mocked `AsyncSession`).

#### 1.2 `services/llm_client.py` — `parse_json_response()` edge cases
**Current coverage: 43%.** The `parse_json_response` function handles markdown-fenced JSON (```` ```json ... ``` ````) and plain JSON. Only the happy path is tested implicitly through metadata extraction.

**Suggested tests:**
- Plain JSON string → parsed dict
- JSON wrapped in ```` ```json ... ``` ```` → parsed dict
- JSON wrapped in ```` ``` ... ``` ```` (no language tag) → parsed dict
- Invalid JSON → raises appropriate error
- Empty string → raises appropriate error

#### 1.3 `services/llm_client.py` — provider validation
**Suggested tests:**
- `llm_complete()` with `LLM_PROVIDER="unsupported"` raises `ValueError`
- `llm_complete()` with `LLM_PROVIDER="openai"` but no API key raises `RuntimeError`

#### 1.4 `config.py` — Settings property parsing
**Suggested tests:**
- `crawl_category_list` with `"cs.AI,cs.CL,cs.CV"` → `["cs.AI", "cs.CL", "cs.CV"]`
- `crawl_category_list` with `"cs.AI, cs.CL , cs.CV"` (whitespace) → trimmed list
- `translation_language_list` with `"zh,ja,es"` → `["zh", "ja", "es"]`

---

### Priority 2: API Endpoint Tests with Database Mocking

#### 2.1 `api/papers.py` — `list_papers()`, `get_paper()`
**Current coverage: 53%.** The list and detail endpoints are completely untested. These are the primary read paths for the application.

**Suggested tests (mock or in-memory DB):**
- `GET /api/v1/papers` with no papers → empty list
- `GET /api/v1/papers` with seeded papers → paginated results
- `GET /api/v1/papers?category=cs.AI` → filtered results
- `GET /api/v1/papers?status=READY` → filtered by status
- `GET /api/v1/papers?page=2&page_size=5` → correct pagination offset
- `GET /api/v1/papers/{id}` with valid ID → paper detail with authors
- `GET /api/v1/papers/{id}` with nonexistent ID → 404

#### 2.2 `api/papers.py` — successful `submit_paper()`
The current tests only cover validation errors. A successful submission path (mocking the crawler and DB) should be tested.

**Suggested tests:**
- `POST /api/v1/papers/submit` with valid `paper_ids` → 200 with results array
- Response contains correct `status` per paper (`"queued"`, `"duplicate"`, `"not_found"`)

---

### Priority 3: Crawler Unit Tests (mocked HTTP)

#### 3.1 `services/crawler/arxiv.py` — `_parse_entry()`, `_parse_datetime()`
**Current coverage: 60%.** The parsing helper functions are only exercised through integration tests that hit the real arXiv API. These should have unit tests with fixture data.

**Suggested tests:**
- `_parse_datetime` with a feedparser time struct → correct UTC datetime
- `_parse_entry` with a sample Atom feed entry dict → correct `CrawledPaper` fields
- `_parse_entry` with missing optional fields → graceful defaults
- `fetch_paper_by_id` with a mocked httpx response (empty Atom feed) → `None`
- `fetch_recent_papers` with mocked feed data → filtered by date

This eliminates the need for network calls while testing the actual parsing logic.

---

### Priority 4: Celery Task Tests

#### 4.1 `tasks/crawl_tasks.py` — `fetch_submitted_paper()`
**Current coverage: 29%.** The task has retry logic (`max_retries=3`, `default_retry_delay=30`) and error handling that is completely untested.

**Suggested tests (mock crawler, no Celery broker needed):**
- Successful fetch returns `{"status": "fetched", ...}`
- Paper not found returns `{"status": "not_found"}`
- Exception triggers `self.retry()`
- Max retries exceeded returns error

#### 4.2 `tasks/parse_tasks.py` — `parse_paper()`
**Current coverage: 0%.** Even though it's a stub, the stub return path should be exercised so coverage catches regressions when the implementation is filled in.

---

### Priority 5: Error Handling and Edge Cases

These are lower priority but important for production robustness:

#### 5.1 `services/parser/pdf_extractor.py` — error paths
- `download_pdf` with an invalid URL → appropriate error
- `download_pdf` with a URL that returns 404 → appropriate error
- `extract_text_from_pdf` with a corrupted/empty PDF → appropriate error

#### 5.2 `services/crawler/arxiv.py` — error paths
- Network timeout during feed fetch
- Malformed XML response
- Rate limiting (HTTP 429)

#### 5.3 `services/translator.py` — additional languages
- Spanish (`es`) translation is configured but never tested
- Unknown language code handling

---

### Priority 6: Schema Validation Tests

#### 6.1 Pydantic model validation in `schemas/paper.py`
- `PaperSearchParams` with `page_size > 100` → validation error
- `SubmitPaperRequest` with invalid `PaperSource` enum value
- `PaperDetail` serialization from ORM model (`model_config = ConfigDict(from_attributes=True)`)

---

## Infrastructure Recommendations

1. **Add an in-memory SQLite fixture for database tests.** The project currently has zero database tests because they require PostgreSQL. An async SQLite session (`aiosqlite`) would allow testing ORM operations, the submission service, and paper API endpoints without Docker.

2. **Mark tests with `pytest.mark` categories.** Separate `@pytest.mark.unit`, `@pytest.mark.integration`, and `@pytest.mark.e2e` so CI can run fast unit tests on every commit and slower integration tests on a schedule.

3. **Add PyMuPDF to the CI test environment.** The `test_fake_llm.py::TestFakeE2EPipeline::test_full_pipeline` test currently fails because `pymupdf` is not installed — this test should either skip gracefully when PyMuPDF is missing (like `test_pdf_extractor_integration.py` does) or PyMuPDF should be ensured in CI.

4. **Mock the arXiv API for unit tests.** Several "offline" tests still make real HTTP calls to `export.arxiv.org`. Using `respx` or `pytest-httpx` to mock these calls would make the test suite fully offline-capable and faster.

5. **Add a `conftest.py` fixture for the fake LLM provider.** The `monkeypatch` pattern in `test_fake_llm.py` is repeated for each test class. A session-scoped fixture that sets `LLM_PROVIDER=fake` would reduce boilerplate.

---

## Summary

| Priority | Area | Current Coverage | Impact |
|----------|------|-----------------|--------|
| P1 | Submission service unit tests | 27% | Tests the core paper ingestion logic |
| P1 | `parse_json_response` + LLM provider validation | 43% | Catches JSON parsing edge cases |
| P1 | Config property parsing | 91% | Quick win for full coverage |
| P2 | Paper list/detail API endpoints | 53% | Tests primary read paths |
| P3 | Crawler parsing helpers (mocked HTTP) | 60% | Eliminates network dependency |
| P4 | Celery task logic (retry, error handling) | 0-29% | Tests async job reliability |
| P5 | Error handling across services | varies | Production robustness |
| P6 | Schema validation | n/a | Input validation correctness |
