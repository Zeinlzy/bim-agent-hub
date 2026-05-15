from __future__ import annotations

import asyncio

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.agents.registry import registry
from app.db.connection import engine
from app.tools.registry import tool_registry

router = APIRouter()

_HEALTH_TIMEOUT = 5


@router.get("/v1/health/live")
async def health_live():
    return {"status": "ok"}


@router.get("/v1/health/ready")
async def health_ready(request: Request):
    components: dict[str, str] = {}
    status = "ok"

    try:
        async with engine.connect() as conn:
            await asyncio.wait_for(
                conn.execute(text("SELECT 1")), timeout=_HEALTH_TIMEOUT
            )
        components["database"] = "ok"
    except Exception as e:
        components["database"] = f"error: {e}"
        status = "degraded"

    redis = getattr(request.app.state, "redis", None)
    if redis is not None:
        try:
            await asyncio.wait_for(redis.ping(), timeout=_HEALTH_TIMEOUT)
            components["redis"] = "ok"
        except Exception as e:
            components["redis"] = f"error: {e}"
            status = "degraded"

    agents_loaded = len(registry.list_agents()) > 0
    tools_loaded = len(tool_registry.list_tools()) > 0
    components["agents_loaded"] = "ok" if agents_loaded else "empty"
    components["tools_loaded"] = "ok" if tools_loaded else "empty"

    code = 200 if status == "ok" else 503
    return JSONResponse({"status": status, "components": components}, status_code=code)


@router.get("/v1/health")
async def health(request: Request):
    return await health_ready(request)
