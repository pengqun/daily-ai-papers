# Development Guide

本地开发环境搭建、测试流程与代码规范。

---

## 环境要求

- **Python** 3.11+
- **PostgreSQL** 17（推荐使用 Docker）
- **Redis** 7
- **系统依赖：** `libmupdf-dev`（PyMuPDF 需要）

---

## 本地搭建

### 1. 克隆项目

```bash
git clone https://github.com/<org>/daily-ai-papers.git
cd daily-ai-papers
```

### 2. 创建虚拟环境并安装依赖

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 3. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，至少配置 LLM API Key（或使用 `LLM_PROVIDER=fake` 进行离线开发）。

详细配置项参见 [CONFIGURATION.md](CONFIGURATION.md)。

### 4. 启动基础服务

使用 Docker Compose 启动 PostgreSQL 和 Redis：

```bash
cd docker
docker compose up -d postgres redis
```

### 5. 启动 API 服务

```bash
uvicorn daily_ai_papers.main:app --reload --port 8000
```

访问 http://localhost:8000/docs 查看 Swagger UI。

### 6.（可选）启动 Celery Worker

```bash
# Worker：执行异步任务
celery -A daily_ai_papers.tasks.celery_app worker --loglevel=info

# Beat：定时调度
celery -A daily_ai_papers.tasks.celery_app beat --loglevel=info
```

---

## 项目结构

```
src/daily_ai_papers/
├── main.py              # FastAPI 入口
├── config.py            # Pydantic Settings 配置
├── database.py          # SQLAlchemy 异步引擎
├── models/              # ORM 模型
├── schemas/             # Pydantic 请求/响应 Schema
├── api/                 # FastAPI 路由（papers, tasks, chat）
├── services/            # 业务逻辑层
│   ├── crawler/         # 论文爬虫（arXiv 等）
│   ├── parser/          # PDF 解析 + LLM 元数据提取
│   ├── llm_client.py    # 统一 LLM 客户端
│   ├── submission.py    # 手动提交工作流
│   └── translator.py    # LLM 翻译
└── tasks/               # Celery 任务定义
```

---

## 测试

项目使用 `pytest` + `pytest-asyncio`，异步模式设为 `auto`，无需手动添加 `@pytest.mark.asyncio`。

### 运行全部测试

```bash
pytest
```

### 运行特定文件

```bash
pytest tests/test_api_integration.py -v
```

### 离线测试（无需 API Key 和数据库）

```bash
pytest tests/test_fake_llm.py -v
```

使用 `LLM_PROVIDER=fake` 可跑通包含 LLM 调用的测试，返回固定的模拟响应。

### 测试覆盖率

```bash
pytest --cov=daily_ai_papers tests/
```

### 测试文件说明

| 文件 | 说明 | 需要网络 | 需要数据库 |
|------|------|----------|------------|
| `test_fake_llm.py` | LLM 客户端模拟测试 | 否 | 否 |
| `test_api_integration.py` | FastAPI 端点测试 | 否 | 是 |
| `test_tasks_api.py` | 任务管理端点测试 | 否 | 否 |
| `test_crawler_integration.py` | arXiv API 集成测试 | 是 | 否 |
| `test_pdf_extractor_integration.py` | PDF 下载和解析测试 | 是 | 否 |
| `test_llm_integration.py` | 真实 LLM 调用测试 | 是 | 否 |
| `test_pipeline_e2e.py` | 端到端流水线测试 | 是 | 是 |

### 测试约定

- 已知测试论文：arXiv ID `1706.03762`（Attention Is All You Need）
- `api_client` fixture 提供 `httpx.AsyncClient`，自动连接到 FastAPI 测试应用
- 共享常量和 fixture 定义在 `tests/conftest.py`

---

## 代码风格

### Linter & Formatter

项目使用 [Ruff](https://docs.astral.sh/ruff/) 统一管理 lint 和格式化。

```bash
# 检查 lint 错误
ruff check src tests

# 自动修复
ruff check --fix src tests

# 格式化代码
ruff format src tests
```

**Ruff 配置（pyproject.toml）：**

- 目标版本：Python 3.11
- 行宽限制：100 字符
- 启用规则：`E`（pycodestyle）, `F`（pyflakes）, `I`（isort）, `N`（命名）, `W`（警告）, `UP`（pyupgrade）, `B`（bugbear）, `SIM`（simplify）

### 类型检查

```bash
mypy src/
```

使用 strict 模式，配合 Pydantic 插件。

### 命名规范

| 类型 | 风格 | 示例 |
|------|------|------|
| 类名 | `PascalCase` | `BaseCrawler`, `PaperDetail` |
| 函数/方法 | `snake_case` | `fetch_recent_papers`, `extract_text_from_pdf` |
| 常量 | `UPPER_CASE` | `ARXIV_API_URL`, `SYSTEM_PROMPT` |
| 私有成员 | `_snake_case` | `_parse_entry`, `_get_crawler` |

### 架构原则

- **Async-first：** 所有 I/O 操作使用 `async/await`（httpx, asyncpg, SQLAlchemy async）
- **分层架构：** API 路由 → 业务服务 → ORM 模型
- **日志：** 每个模块使用 `logging.getLogger(__name__)`
- **配置：** 统一通过 `pydantic-settings` 从 `.env` 读取

---

## 添加新的爬虫源

1. 在 `services/crawler/` 下创建新文件，继承 `BaseCrawler`
2. 实现 `fetch_recent_papers()` 和 `fetch_paper_by_id()` 两个抽象方法
3. 返回 `CrawledPaper` 数据类
4. 在 `schemas/paper.py` 的 `PaperSource` 枚举中添加新来源
5. 在提交工作流 `services/submission.py` 中注册新爬虫

```python
from daily_ai_papers.services.crawler.base import BaseCrawler, CrawledPaper

class NewSourceCrawler(BaseCrawler):
    async def fetch_recent_papers(
        self, categories: list[str], max_results: int = 100, days_back: int = 1
    ) -> list[CrawledPaper]:
        ...

    async def fetch_paper_by_id(self, paper_id: str) -> CrawledPaper | None:
        ...
```

---

## 添加新的 API 端点

1. 在 `api/` 下的相应文件中添加路由函数
2. 在 `schemas/` 中定义请求/响应 Pydantic 模型
3. 业务逻辑放在 `services/` 层
4. 如需新路由模块，在 `main.py` 中注册：

```python
app.include_router(new_router, prefix="/api/v1/new", tags=["new"])
```

---

## Pre-commit Hooks

项目配置了 pre-commit hooks。首次安装：

```bash
pre-commit install
```

每次 commit 前会自动运行 Ruff 检查和格式化。
