# Deployment Guide

Docker 部署、生产环境配置与运维指南。

---

## Docker Compose 一键部署

项目提供了完整的 Docker Compose 配置，包含 5 个服务。

### 快速启动

```bash
cp .env.example .env
# 编辑 .env，配置 LLM_API_KEY 等必要参数

cd docker
docker compose up -d
```

### 服务列表

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| `api` | 自构建 | 8000 | FastAPI 应用（开发模式下开启热重载） |
| `worker` | 自构建 | — | Celery Worker，执行异步任务 |
| `beat` | 自构建 | — | Celery Beat，定时调度（每日爬取） |
| `postgres` | pgvector/pgvector:pg17 | 5432 | PostgreSQL 17 + pgvector 扩展 |
| `redis` | redis:7-alpine | 6379 | Redis 7，作为 Celery Broker |

### 架构拓扑

```
                     ┌─────────┐
  用户请求 ──────────►│   api   │:8000
                     └────┬────┘
                          │
            ┌─────────────┼─────────────┐
            │             │             │
       ┌────▼────┐  ┌─────▼─────┐ ┌────▼────┐
       │ postgres │  │   redis   │ │ worker  │
       │  :5432   │  │   :6379   │ │         │
       └─────────┘  └─────┬─────┘ └─────────┘
                          │
                     ┌────▼────┐
                     │  beat   │
                     └─────────┘
```

### 健康检查

PostgreSQL 和 Redis 配置了健康检查，api、worker、beat 服务会等待依赖服务就绪后才启动。

```bash
# 查看服务状态
docker compose ps

# 查看服务日志
docker compose logs -f api
docker compose logs -f worker
```

---

## Dockerfile 说明

```dockerfile
FROM python:3.11-slim

# 安装 PyMuPDF 所需的系统依赖
RUN apt-get update && apt-get install -y libmupdf-dev

# 安装 Python 包
COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir .
```

镜像基于 `python:3.11-slim`，仅安装运行时必需的 `libmupdf-dev` 系统包。

---

## 生产环境注意事项

### 数据库

- **持久化：** docker-compose 中 `pgdata` volume 确保数据持久化
- **连接池：** SQLAlchemy 默认使用连接池，生产环境可调整 `pool_size` 和 `max_overflow`
- **备份：** 定期对 PostgreSQL 进行 `pg_dump` 备份

```bash
# 手动备份
docker compose exec postgres pg_dump -U postgres daily_ai_papers > backup.sql

# 恢复
docker compose exec -T postgres psql -U postgres daily_ai_papers < backup.sql
```

### 安全

- **修改默认密码：** 生产环境务必修改 `.env` 中的 PostgreSQL 用户名和密码
- **API Key 保护：** 确保 `.env` 文件不被提交到版本控制（已在 `.gitignore` 中）
- **网络隔离：** 仅暴露 api 服务的 8000 端口，其他服务（postgres, redis）不对外开放

### 反向代理

生产部署推荐在 API 前配置 Nginx 或 Caddy 作为反向代理：

```nginx
server {
    listen 80;
    server_name papers.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Celery Worker 扩容

可通过增加 worker 副本数来扩容：

```bash
docker compose up -d --scale worker=3
```

或者调整 worker 的并发数：

```yaml
command: celery -A daily_ai_papers.tasks.celery_app worker --loglevel=info --concurrency=4
```

---

## 常用运维操作

### 查看服务状态

```bash
docker compose ps
docker compose logs --tail=50 api
```

### 手动触发爬取

```bash
curl -X POST http://localhost:8000/api/v1/tasks/crawl
```

### 查看任务状态

```bash
curl http://localhost:8000/api/v1/tasks/<task_id>
```

### 重建并重启

```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

### 仅重启某个服务

```bash
docker compose restart worker
```

### 清理数据

```bash
# 停止并移除所有容器和数据卷（会删除数据库数据！）
docker compose down -v
```

---

## 监控与日志

### 应用日志

每个模块使用 `logging.getLogger(__name__)`，日志输出到标准输出。

通过 Docker 查看：

```bash
docker compose logs -f api worker beat
```

### 健康检查端点

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

### Celery 监控

可使用 [Flower](https://flower.readthedocs.io/) 对 Celery 任务进行可视化监控：

```bash
pip install flower
celery -A daily_ai_papers.tasks.celery_app flower --port=5555
```

访问 http://localhost:5555 查看任务队列、Worker 状态和任务历史。

---

## 故障排查

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| api 启动失败 | PostgreSQL 未就绪 | 检查 `docker compose ps`，确认 postgres 健康 |
| worker 无法连接 Redis | Redis 未启动 | `docker compose up -d redis` |
| 爬取任务无响应 | worker 未运行 | `docker compose up -d worker` |
| PDF 解析失败 | libmupdf 未安装 | 确认 Dockerfile 中的系统依赖 |
| LLM 调用报错 | API Key 无效或未配置 | 检查 `.env` 中的 `LLM_API_KEY` |
| 数据库连接拒绝 | DATABASE_URL 配置错误 | Docker 内使用 `postgres` 主机名，本地使用 `localhost` |
