from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.usage import UsageLogInfo, UsageLogListResponse, UsageStatsResponse, UsageSummary
from app.services.usage_service import usage_service

router = APIRouter()


@router.get("/v1/usage/summary", response_model=UsageStatsResponse)
async def get_usage_summary(
    since: str | None = Query(None),
    until: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    since_dt = datetime.fromisoformat(since) if since else None
    until_dt = datetime.fromisoformat(until) if until else None

    total = await usage_service.get_summary(db, since=since_dt, until=until_dt)
    by_agent = await usage_service.get_summary_by_agent(db, since=since_dt, until=until_dt)

    return UsageStatsResponse(total=total, by_agent=by_agent)


@router.get("/v1/usage/agents/{agent_id}", response_model=UsageLogListResponse)
async def get_agent_usage(
    agent_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    logs, total = await usage_service.get_logs(db, agent_id=agent_id, limit=limit, offset=offset)
    return UsageLogListResponse(
        logs=[
            UsageLogInfo(
                id=str(log.id),
                session_id=str(log.session_id) if log.session_id else None,
                agent_id=log.agent_id,
                model=log.model,
                input_tokens=log.input_tokens,
                output_tokens=log.output_tokens,
                total_tokens=log.total_tokens,
                cached_tokens=log.cached_tokens,
                reasoning_tokens=log.reasoning_tokens,
                duration_ms=log.duration_ms,
                created_at=log.created_at,
            )
            for log in logs
        ],
        total=total,
    )
