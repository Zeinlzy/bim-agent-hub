# OpenAI Agent SDK Docker API 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a FastAPI HTTP gateway wrapping OpenAI Agents SDK, deployable via Docker.

**Architecture:** Single container with FastAPI serving REST endpoints that delegate to `AgentService` which instantiates and runs OpenAI Agents SDK agents. Streaming via SSE. Multi-stage Docker build.

**Tech Stack:** FastAPI, OpenAI Agents SDK (`openai-agents`), Python 3.12-slim, Uvicorn, Docker

---

### Task 1: Project scaffolding and configuration

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `app/__init__.py`
- Create: `app/config.py`
- Create: `app/agents/__init__.py`
- Create: `app/api/__init__.py`
- Create: `app/schemas/__init__.py`
- Create: `app/services/__init__.py`
- Create: `app/tools/__init__.py`

- [ ] **Step 1: Create requirements.txt**

```
openai-agents>=0.1.0
fastapi>=0.115.0
uvicorn[standard]>=0.34.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
```

- [ ] **Step 2: Create .env.example**

```bash
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
PORT=8000
LOG_LEVEL=info
```

- [ ] **Step 3: Create all `__init__.py` files (empty)**

Create empty `__init__.py` in `app/`, `app/agents/`, `app/api/`, `app/schemas/`, `app/services/`, `app/tools/`.

- [ ] **Step 4: Create app/config.py**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    port: int = 8000
    log_level: str = "info"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
```

---

### Task 2: Agent definitions and registry

**Files:**
- Create: `app/agents/definitions.py`
- Create: `app/agents/registry.py`

- [ ] **Step 1: Create app/agents/definitions.py**

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class AgentConfig:
    name: str
    instructions: str
    model: str | None = None
    tools: list[Callable] = field(default_factory=list)
    handoff_agents: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
```

- [ ] **Step 2: Create app/agents/registry.py**

```python
from __future__ import annotations

from agents import Agent as OpenAIAgent

from app.agents.definitions import AgentConfig
from app.config import settings


class AgentRegistry:
    """Registry that holds agent configurations and creates SDK agent instances."""

    def __init__(self):
        self._configs: dict[str, AgentConfig] = {}

    def register(self, config: AgentConfig) -> None:
        self._configs[config.name] = config

    def get_config(self, agent_id: str) -> AgentConfig | None:
        return self._configs.get(agent_id)

    def list_agents(self) -> list[dict]:
        return [
            {"id": name, "name": cfg.name, "metadata": cfg.metadata}
            for name, cfg in self._configs.items()
        ]

    def build_agent(self, agent_id: str) -> OpenAIAgent:
        config = self._configs.get(agent_id)
        if not config:
            raise ValueError(f"Unknown agent: {agent_id}")
        return OpenAIAgent(
            name=config.name,
            instructions=config.instructions,
            model=config.model or settings.openai_model,
            tools=config.tools or [],
        )


# Default registry instance
registry = AgentRegistry()


def register_default_agents() -> None:
    """Register built-in agents at startup."""
    registry.register(
        AgentConfig(
            name="assistant",
            instructions="You are a helpful assistant.",
        )
    )
```

---

### Task 3: Tool registry

**Files:**
- Create: `app/tools/registry.py`

- [ ] **Step 1: Create app/tools/registry.py**

```python
from __future__ import annotations

from typing import Any, Callable

from agents import function_tool


class ToolRegistry:
    """Registry for tools that agents can use.

    In-memory implementation for the advanced version.
    Future: add persistence, dynamic registration via API.
    """

    def __init__(self):
        self._tools: dict[str, Callable] = {}

    def register(self, fn: Callable, name: str | None = None) -> Callable:
        key = name or fn.__name__
        wrapped = function_tool(fn)
        self._tools[key] = wrapped
        return wrapped

    def get_tool(self, name: str) -> Callable | None:
        return self._tools.get(name)

    def get_all_tools(self) -> list[Callable]:
        return list(self._tools.values())

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {"name": name, "description": getattr(tool, "__doc__", "") or ""}
            for name, tool in self._tools.items()
        ]


# Default registry instance
tool_registry = ToolRegistry()


def register_default_tools() -> None:
    """Register built-in example tools."""

    @tool_registry.register
    def get_current_time() -> str:
        """Get the current date and time."""
        from datetime import datetime

        return datetime.now().isoformat()

    @tool_registry.register
    def echo(text: str) -> str:
        """Echo the input text back."""
        return text
```

---

### Task 4: Request/response schemas

**Files:**
- Create: `app/schemas/chat.py`
- Create: `app/schemas/agents.py`

- [ ] **Step 1: Create app/schemas/chat.py**

```python
from __future__ import annotations

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str = "user"
    content: str


class ChatCompletionRequest(BaseModel):
    messages: list[ChatMessage]
    model: str | None = None
    stream: bool = False
    agent_id: str = "assistant"


class ChatCompletionChoice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: str = "stop"


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    choices: list[ChatCompletionChoice]


class AgentChatRequest(BaseModel):
    messages: list[ChatMessage]
    stream: bool = False


class AgentChatResponse(BaseModel):
    id: str
    agent_id: str
    content: str
```

- [ ] **Step 2: Create app/schemas/agents.py**

```python
from __future__ import annotations

from pydantic import BaseModel


class AgentInfo(BaseModel):
    id: str
    name: str
    metadata: dict = {}


class AgentListResponse(BaseModel):
    agents: list[AgentInfo]
```

---

### Task 5: Agent service

**Files:**
- Create: `app/services/agent_service.py`

- [ ] **Step 1: Create app/services/agent_service.py**

```python
from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

from agents import Runner, trace

from app.agents.registry import registry
from app.config import settings
from app.tools.registry import tool_registry


class AgentService:
    """Orchestrates a single agent invocation: resolve agent, run, return result."""

    async def run(
        self,
        agent_id: str,
        messages: list[dict],
        model_override: str | None = None,
    ) -> str:
        config = registry.get_config(agent_id)
        if config and config.tools:
            config.tools = tool_registry.get_all_tools()

        agent = registry.build_agent(agent_id)

        with trace(workflow_name=agent_id, group_id=uuid.uuid4().hex):
            result = await Runner.run(agent, input=messages)

        return result.final_output

    async def run_stream(
        self,
        agent_id: str,
        messages: list[dict],
        model_override: str | None = None,
    ) -> AsyncGenerator[str, None]:
        config = registry.get_config(agent_id)
        if config and config.tools:
            config.tools = tool_registry.get_all_tools()

        agent = registry.build_agent(agent_id)

        with trace(workflow_name=agent_id, group_id=uuid.uuid4().hex):
            result = Runner.run_streamed(agent, input=messages)

            async for event in result.stream_raw_responses():
                yield event.delta or ""


agent_service = AgentService()
```

---

### Task 6: API routes

**Files:**
- Create: `app/api/chat.py`
- Create: `app/api/agents.py`

- [ ] **Step 1: Create app/api/chat.py**

```python
from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.chat import (
    AgentChatRequest,
    AgentChatResponse,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatMessage,
)
from app.services.agent_service import agent_service

router = APIRouter()


@router.post("/v1/chat/completions")
async def chat_completions(body: ChatCompletionRequest):
    messages = [m.model_dump() for m in body.messages]
    agent_id = body.agent_id

    try:
        if body.stream:
            return _stream_response(agent_id, messages)
        content = await agent_service.run(agent_id, messages)
        return ChatCompletionResponse(
            id=uuid.uuid4().hex,
            choices=[
                ChatCompletionChoice(
                    message=ChatMessage(role="assistant", content=content)
                )
            ],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v1/agents/{agent_id}/chat")
async def agent_chat(agent_id: str, body: AgentChatRequest):
    messages = [m.model_dump() for m in body.messages]

    try:
        if body.stream:
            return _stream_response(agent_id, messages)
        content = await agent_service.run(agent_id, messages)
        return AgentChatResponse(
            id=uuid.uuid4().hex,
            agent_id=agent_id,
            content=content,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _stream_response(agent_id: str, messages: list[dict]):
    """Return a StreamingResponse that yields SSE-encoded chunks."""

    async def event_stream():
        async for delta in agent_service.run_stream(agent_id, messages):
            chunk = {
                "id": uuid.uuid4().hex,
                "object": "chat.completion.chunk",
                "choices": [{"delta": {"content": delta}, "index": 0}],
            }
            yield f"data: {json.dumps(chunk)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

- [ ] **Step 2: Create app/api/agents.py**

```python
from __future__ import annotations

from fastapi import APIRouter

from app.agents.registry import registry
from app.schemas.agents import AgentInfo, AgentListResponse

router = APIRouter()


@router.get("/v1/agents", response_model=AgentListResponse)
async def list_agents():
    agents = registry.list_agents()
    return AgentListResponse(
        agents=[AgentInfo(**a) for a in agents]
    )
```

---

### Task 7: FastAPI app entry point

**Files:**
- Create: `app/main.py`

- [ ] **Step 1: Create app/main.py**

```python
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.agents.registry import register_default_agents
from app.api import chat as chat_router
from app.api import agents as agents_router
from app.tools.registry import register_default_tools


@asynccontextmanager
async def lifespan(app: FastAPI):
    register_default_agents()
    register_default_tools()
    yield


app = FastAPI(
    title="OpenAI Agent API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(chat_router.router)
app.include_router(agents_router.router)


@app.get("/v1/health")
async def health():
    return JSONResponse({"status": "ok"})
```

---

### Task 8: Dockerfile

**Files:**
- Create: `Dockerfile`

- [ ] **Step 1: Create Dockerfile**

```dockerfile
# ===== Build stage =====
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/build/deps -r requirements.txt

# ===== Runtime stage =====
FROM python:3.12-slim

ENV PORT=8000

COPY --from=builder /build/deps /usr/local

WORKDIR /app
COPY ./app ./app

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/v1/health')"

EXPOSE ${PORT}
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
```

---

### Task 9: Docker Compose

**Files:**
- Create: `docker-compose.yml`

- [ ] **Step 1: Create docker-compose.yml**

```yaml
services:
  api:
    build: .
    ports:
      - "${PORT:-8000}:8000"
    env_file:
      - .env
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/v1/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

### Task 10: Verify Docker build

- [ ] **Step 1: Build the Docker image**

```bash
cd /d/bim-agent-hub
docker compose build
```

Expected: Build succeeds with no errors.

- [ ] **Step 2: Verify project file tree**

```bash
cd /d/bim-agent-hub && find . -type f | sort
```

Expected: All project files present.
