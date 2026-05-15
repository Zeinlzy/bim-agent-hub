from __future__ import annotations

import os
from contextlib import asynccontextmanager

from redis.asyncio import Redis

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agents.seed import seed_default_agents
from app.api import chat as chat_router
from app.api import agents as agents_router
from app.api import admin_api_keys as admin_keys_router
from app.api import health as health_router
from app.api import conversations as conversations_router
from app.api import tools as tools_router
from app.api import usage as usage_router
from app.config import settings
from app.core.exceptions import AppError
from app.core.logging import setup_logging
from app.db.connection import dispose_db
from app.middleware.auth import AuthMiddleware
from app.middleware.error_handler import app_error_handler, unhandled_error_handler
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.tools.registry import register_default_tools

setup_logging()
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)
    os.environ.setdefault("OPENAI_BASE_URL", settings.openai_base_url)

    if settings.run_migrations_on_startup:
        from alembic.config import Config as AlembicConfig
        from alembic.script import ScriptDirectory
        from alembic.runtime.migration import MigrationContext
        from app.db.connection import engine

        alembic_cfg = AlembicConfig("alembic.ini")
        script = ScriptDirectory.from_config(alembic_cfg)
        async with engine.connect() as conn:
            current = await conn.run_sync(
                lambda sync_conn: MigrationContext.configure(sync_conn).get_current_revision()
            )
        head = script.get_current_head()
        if current != head:
            from alembic import command
            command.upgrade(alembic_cfg, "head")

    app.state.redis = None
    if settings.redis_url:
        try:
            app.state.redis = Redis.from_url(settings.redis_url, decode_responses=True)
            await app.state.redis.ping()
        except Exception as e:
            logger.warning("Redis unavailable: %s", e)
            app.state.redis = None

    if settings.tool_dynamic_exec_enabled:
        logger.warning(
            "tool_dynamic_exec_enabled=True — user-submitted Python code will be executed "
            "via exec() IN-PROCESS without subprocess isolation. "
            "Only enable if all users with POST /v1/tools access are fully trusted."
        )

    await seed_default_agents()
    await register_default_tools()

    yield

    if app.state.redis:
        await app.state.redis.close()
    await dispose_db()


app = FastAPI(
    title="OpenAI Agent API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuthMiddleware)
app.add_middleware(RateLimitMiddleware)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)

app.include_router(health_router.router)
app.include_router(chat_router.router)
app.include_router(agents_router.router)
app.include_router(tools_router.router)
app.include_router(conversations_router.router)
app.include_router(admin_keys_router.router)
app.include_router(usage_router.router)
