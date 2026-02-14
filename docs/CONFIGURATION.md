# Configuration Reference

所有配置通过环境变量管理，由 [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) 加载。支持 `.env` 文件和系统环境变量，系统环境变量优先。

---

## 快速配置

```bash
cp .env.example .env
```

最小可用配置只需设置 LLM 相关参数。如果仅做本地开发测试，可将 `LLM_PROVIDER` 设为 `fake` 跳过 LLM API 调用。

---

## 完整参数列表

### 数据库

| 变量 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `DATABASE_URL` | string | `postgresql+asyncpg://postgres:postgres@localhost:5432/daily_ai_papers` | PostgreSQL 异步连接字符串。Docker 环境中主机名用 `postgres`，本地开发用 `localhost` |

连接字符串格式：`postgresql+asyncpg://<user>:<password>@<host>:<port>/<database>`

### Redis

| 变量 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `REDIS_URL` | string | `redis://localhost:6379/0` | Redis 连接 URL，用于 Celery Broker。Docker 环境中主机名用 `redis` |

### LLM

| 变量 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `LLM_PROVIDER` | string | `openai` | LLM 服务提供方。可选：`openai`, `anthropic`, `fake` |
| `LLM_API_KEY` | string | `""` | LLM API Key。`fake` 模式下无需配置 |
| `LLM_BASE_URL` | string | `""` | 自定义 API 端点 URL。用于接入 Groq、OpenRouter 等 OpenAI 兼容服务 |
| `LLM_MODEL` | string | `gpt-4o-mini` | 模型名称。不同 provider 需配置对应的模型名 |
| `EMBEDDING_MODEL` | string | `text-embedding-3-small` | 文本嵌入模型名称（Phase 4 实现时使用） |

### 爬虫

| 变量 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `CRAWL_SCHEDULE_HOUR` | int | `6` | 每日自动爬取的 UTC 小时数（0-23） |
| `CRAWL_CATEGORIES` | string | `cs.AI,cs.CL,cs.CV,cs.LG,stat.ML` | 逗号分隔的 arXiv 分类列表 |
| `CRAWL_MAX_RESULTS` | int | `100` | 每次爬取的最大论文数 |
| `CRAWL_DAYS_BACK` | int | `1` | 爬取最近多少天内发表的论文 |

### 翻译

| 变量 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `TRANSLATION_LANGUAGES` | string | `zh,ja,es` | 逗号分隔的目标翻译语言代码 |

**支持的语言代码：**

| 代码 | 语言 |
|------|------|
| `zh` | 中文 |
| `ja` | 日语 |
| `es` | 西班牙语 |
| `fr` | 法语 |
| `de` | 德语 |
| `ko` | 韩语 |

---

## LLM Provider 配置示例

### OpenAI（默认）

```env
LLM_PROVIDER=openai
LLM_API_KEY=sk-your-key-here
LLM_MODEL=gpt-4o-mini
```

### Anthropic

```env
LLM_PROVIDER=anthropic
LLM_API_KEY=sk-ant-your-key-here
LLM_MODEL=claude-sonnet-4-20250514
```

### Groq（免费，OpenAI 兼容）

```env
LLM_PROVIDER=openai
LLM_API_KEY=gsk_your-key-here
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile
```

### OpenRouter（免费额度）

```env
LLM_PROVIDER=openai
LLM_API_KEY=sk-or-your-key-here
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=deepseek/deepseek-r1:free
```

### Google AI Studio / Gemini（免费）

```env
LLM_PROVIDER=openai
LLM_API_KEY=AIza-your-key-here
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_MODEL=gemini-2.0-flash
```

### Cerebras（免费）

```env
LLM_PROVIDER=openai
LLM_API_KEY=csk-your-key-here
LLM_BASE_URL=https://api.cerebras.ai/v1
LLM_MODEL=llama-3.3-70b
```

### Fake（离线测试）

```env
LLM_PROVIDER=fake
```

`fake` 模式返回预设的模拟响应，无需 API Key，适用于：
- 本地开发调试
- CI/CD 自动化测试
- 无网络环境下的功能验证

---

## Docker 环境差异

在 Docker Compose 环境中，服务间通过容器名通信，需要注意主机名配置：

| 变量 | 本地开发 | Docker 内 |
|------|----------|-----------|
| `DATABASE_URL` | `...@localhost:5432/...` | `...@postgres:5432/...` |
| `REDIS_URL` | `redis://localhost:6379/0` | `redis://redis:6379/0` |

docker-compose.yml 中各服务通过 `env_file: ../.env` 加载项目根目录的 `.env` 文件。

---

## arXiv 分类参考

`CRAWL_CATEGORIES` 中常用的 AI/ML 相关 arXiv 分类：

| 分类 | 全称 |
|------|------|
| `cs.AI` | Artificial Intelligence |
| `cs.CL` | Computation and Language (NLP) |
| `cs.CV` | Computer Vision and Pattern Recognition |
| `cs.LG` | Machine Learning |
| `cs.NE` | Neural and Evolutionary Computing |
| `cs.IR` | Information Retrieval |
| `cs.RO` | Robotics |
| `stat.ML` | Machine Learning (Statistics) |

完整分类列表参见 [arXiv 分类说明](https://arxiv.org/category_taxonomy)。
