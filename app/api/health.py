from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.db.connection import engine

router = APIRouter()


@router.get("/v1/health")
async def health(request: Request):
    components: dict[str, str] = {}
    status = "ok"

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        components["database"] = "ok"
    except Exception as e:
        components["database"] = f"error: {e}"
        status = "degraded"

    redis = getattr(request.app.state, "redis", None)
    if redis is not None:
        try:
            await redis.ping()
            components["redis"] = "ok"
        except Exception as e:
            components["redis"] = f"error: {e}"
            status = "degraded"

    code = 200 if status == "ok" else 503
    return JSONResponse(
        {"status": status, "components": components},
        status_code=code,
    )
