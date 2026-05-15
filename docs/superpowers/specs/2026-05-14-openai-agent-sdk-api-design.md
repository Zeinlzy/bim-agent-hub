# OpenAI Agent SDK — Docker API 网关设计

## 概述

将 OpenAI Agents SDK 包装为 FastAPI HTTP 服务，部署在 Docker 中，通过 REST API 暴露 Agent 调用能力。进阶版先行，架构为完整版预留扩展点。

## 项目结构

```
openai-agent-api/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI 应用入口
│   ├── config.py                # 配置（API Key、模型默认值等）
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── registry.py          # Agent 注册、查找、实例化
│   │   └── definitions.py       # AgentConfig 数据模型
│   ├── services/
│   │   ├── __init__.py
│   │   └── agent_service.py     # 编排 Agent 一次调用全流程
│   ├── api/
│   │   ├── __init__.py
│   │   ├── chat.py              # 聊天端点（流式/非流式）
│   │   └── agents.py            # GET /v1/agents
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── chat.py              # 请求/响应 Pydantic 模型
│   │   └── agents.py
│   └── tools/
│       ├── __init__.py
│       └── registry.py          # 工具注册接口 + 内存实现
├── Dockerfile                   # 多阶段构建
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

### 分层职责

| 层 | 职责 | 备注 |
|---|---|---|
| `api/` | HTTP 协议处理、入参校验、响应序列化 | 后续拆 Worker 时不动 |
| `services/` | 编排 Agent 执行、异常处理、重试 | 替换实现即可切换执行模式 |
| `agents/` | Agent 定义与配置管理 | 不关心 HTTP |
| `tools/` | 工具注册框架 | 进阶版内置示例工具，完整版动态注册 |

## API 端点

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/v1/health` | 健康检查（Docker HEALTHCHECK 使用） |
| `POST` | `/v1/chat/completions` | 兼容 OpenAI Chat API 格式，支持 `stream: true` SSE |
| `POST` | `/v1/agents/{agent_id}/chat` | 指定 Agent 运行，`?stream=true` 控制流式 |
| `GET` | `/v1/agents` | 列出已注册 Agents |

- Streaming 使用 SSE (`text/event-stream`)，chunk 格式兼容 OpenAI API
- 错误统一返回 `{"error": {"code": "...", "message": "..."}}`

## Agent 管理（进阶版）

- 启动时从配置/代码注册一组预定义 Agent
- 每个 Agent 包含：name、instructions、tools、handoffs 等
- 完整版扩展为运行时 CRUD

## Docker 部署

### Dockerfile（多阶段构建）

```
阶段 1 (builder)   → python:3.12-slim，pip install 到 /build/deps
阶段 2 (runtime)   → python:3.12-slim，复制依赖 + 代码
```

- 可选端口 `PORT` 环境变量，默认 8000
- HEALTHCHECK 使用 Python `urllib`（无需 curl）
- 启动命令：`uvicorn app.main:app --host 0.0.0.0 --port ${PORT}`

### docker-compose

- `api` 服务，映射端口 8000
- 通过 `env_file` 注入环境变量（`OPENAI_API_KEY` 等）
- 完整版扩展：加 `redis`、`worker` 等服务

## 完整版预留扩展

- `POST /v1/tools/register` — 动态注册工具
- `POST/DELETE /v1/agents` — Agent CRUD
- `GET /v1/chat/{session_id}/history` — 会话历史
- Redis 队列 + 独立 Agent Worker 进程
