from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.agents.registry import register_default_agents
from app.api import chat as chat_router
from app.api import agents as agents_router
from app.config import settings
from app.tools.registry import register_default_tools


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)
    os.environ.setdefault("OPENAI_BASE_URL", settings.openai_base_url)
    register_default_agents()
    register_default_tools()
    yield


app = FastAPI(
    title="OpenAI Agent API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router.router)
app.include_router(agents_router.router)


@app.get("/v1/health")
async def health():
    return JSONResponse({"status": "ok"})
