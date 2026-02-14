# API Reference

本文档详细描述 daily-ai-papers 提供的全部 REST API 端点。

**Base URL:** `http://localhost:8000`

启动后可通过 `/docs`（Swagger UI）或 `/redoc`（ReDoc）访问自动生成的交互式文档。

---

## Health Check

### `GET /health`

检查服务是否正常运行。

**Response:**

```json
{
  "status": "ok"
}
```

---

## Papers

所有论文相关端点挂载在 `/api/v1/papers` 下。

### `GET /api/v1/papers`

分页获取论文列表，支持按分类和状态过滤。

**Query Parameters:**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `page` | int | 1 | 页码（>=1） |
| `page_size` | int | 20 | 每页条数（1-100） |
| `category` | string | — | 按 arXiv 分类过滤，如 `cs.AI` |
| `status` | string | — | 按处理状态过滤，如 `crawled` |

**Response:** `200 OK`

```json
[
  {
    "id": 1,
    "source": "arxiv",
    "source_id": "1706.03762",
    "title": "Attention Is All You Need",
    "abstract": "The dominant sequence transduction models...",
    "published_at": "2017-06-12T00:00:00Z",
    "categories": ["cs.CL", "cs.LG"],
    "keywords": ["transformer", "attention"],
    "status": "crawled",
    "authors": [
      {
        "id": 1,
        "name": "Ashish Vaswani",
        "affiliation": "Google Brain"
      }
    ]
  }
]
```

---

### `GET /api/v1/papers/{paper_id}`

获取单篇论文的完整详情。

**Path Parameters:**

| 参数 | 类型 | 说明 |
|------|------|------|
| `paper_id` | int | 论文的数据库 ID |

**Response:** `200 OK`

```json
{
  "id": 1,
  "source": "arxiv",
  "source_id": "1706.03762",
  "title": "Attention Is All You Need",
  "abstract": "...",
  "published_at": "2017-06-12T00:00:00Z",
  "categories": ["cs.CL", "cs.LG"],
  "keywords": ["transformer", "attention"],
  "status": "crawled",
  "authors": [...],
  "summary": "This paper proposes the Transformer...",
  "summary_zh": "本文提出了 Transformer...",
  "contributions": [
    "Introduced the Transformer architecture",
    "Achieved new SOTA on WMT translation"
  ],
  "pdf_url": "https://arxiv.org/pdf/1706.03762v5",
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T12:30:00Z"
}
```

**Error:** `404 Not Found` — 论文不存在。

---

### `POST /api/v1/papers/submit`

手动提交论文 ID 进行爬取和处理。支持批量提交（最多 50 篇），自动去重。

**Request Body:**

```json
{
  "source": "arxiv",
  "paper_ids": ["1706.03762", "2401.00001"]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `source` | string | 否 | 论文来源，默认 `arxiv`。可选：`arxiv`, `semantic_scholar` |
| `paper_ids` | string[] | 是 | 来源对应的论文 ID 列表（1-50 条） |

**Response:** `200 OK`

```json
{
  "total": 2,
  "results": [
    {
      "source_id": "1706.03762",
      "status": "queued",
      "paper_id": 1,
      "message": "Paper queued for processing: Attention Is All You Need"
    },
    {
      "source_id": "2401.00001",
      "status": "duplicate",
      "paper_id": 5,
      "message": "Paper already exists (id=5)"
    }
  ]
}
```

**Result status 含义：**

| status | 说明 |
|--------|------|
| `queued` | 新论文，已入库并排队处理 |
| `duplicate` | 论文已存在于数据库中 |
| `not_found` | 在来源 API 中未找到该 ID |
| `error` | 获取过程中发生意外错误 |

---

## Tasks

任务管理端点挂载在 `/api/v1/tasks` 下。

### `POST /api/v1/tasks/crawl`

手动触发一次论文爬取任务（通过 Celery 异步执行）。

**Request Body:** 无

**Response:** `200 OK`

```json
{
  "status": "dispatched",
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

### `GET /api/v1/tasks/{task_id}`

查询异步任务的执行状态。

**Path Parameters:**

| 参数 | 类型 | 说明 |
|------|------|------|
| `task_id` | string | 任务 ID（由触发端点返回） |

**Response:** `200 OK`

```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "SUCCESS",
  "result": "Crawled 42 papers"
}
```

**可能的 status 值：**

| status | 说明 |
|--------|------|
| `PENDING` | 任务已提交，尚未开始执行 |
| `STARTED` | 任务正在执行 |
| `SUCCESS` | 任务执行成功（包含 `result` 字段） |
| `FAILURE` | 任务执行失败（包含 `error` 字段） |
| `RETRY` | 任务正在重试 |

---

## Chat（计划中）

聊天端点挂载在 `/api/v1/chat` 下。当前为桩实现，将在 Phase 6 实现完整的 RAG 管道。

### `POST /api/v1/chat`

基于论文内容的问答（RAG）。

**Request Body:**

```json
{
  "question": "Transformer 的自注意力机制是如何工作的？",
  "paper_ids": [1, 2]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `question` | string | 是 | 用户的提问 |
| `paper_ids` | int[] | 否 | 限定搜索范围的论文 ID。为空则检索全部论文 |

**Response:** `200 OK`

```json
{
  "answer": "自注意力机制通过计算...",
  "source_papers": [1],
  "source_chunks": ["The Transformer uses self-attention to..."]
}
```

---

## 论文处理状态流转

论文从入库到可用，经历以下状态：

```
PENDING → CRAWLED → DOWNLOADING → PARSED → ANALYZED → EMBEDDED → READY
```

| 状态 | 说明 |
|------|------|
| `pending` | 已知来源 URL，尚未获取 |
| `crawled` | 已从来源 API 获取元数据 |
| `downloading` | 正在下载 PDF |
| `parsed` | 已从 PDF 中提取全文 |
| `analyzed` | LLM 已提取摘要、贡献、关键词 |
| `embedded` | 文本块已嵌入向量数据库 |
| `ready` | 全部处理完成，可用于搜索和聊天 |
| `failed` | 处理过程中某阶段失败 |

---

## 错误响应格式

API 使用标准 HTTP 状态码。错误响应遵循 FastAPI 默认格式：

```json
{
  "detail": "Paper not found"
}
```

常见状态码：

| 状态码 | 说明 |
|--------|------|
| `200` | 请求成功 |
| `404` | 资源不存在 |
| `422` | 请求参数验证失败 |
| `500` | 服务器内部错误 |
