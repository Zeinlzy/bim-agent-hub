from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usage_log import UsageLogModel


class UsageLogRepository:
    async def create(
        self,
        db: AsyncSession,
        *,
        session_id: uuid.UUID | None = None,
        agent_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int,
        cached_tokens: int = 0,
        reasoning_tokens: int = 0,
        requests: int = 0,
        duration_ms: int | None = None,
    ) -> UsageLogModel:
        log = UsageLogModel(
            session_id=session_id,
            agent_id=agent_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cached_tokens=cached_tokens,
            reasoning_tokens=reasoning_tokens,
            requests=requests,
            duration_ms=duration_ms,
        )
        db.add(log)
        await db.flush()
        return log

    async def get_summary(
        self, db: AsyncSession, since: datetime | None = None, until: datetime | None = None
    ) -> tuple[int, int, int, int]:
        query = select(
            sa_func.coalesce(sa_func.sum(UsageLogModel.input_tokens), 0),
            sa_func.coalesce(sa_func.sum(UsageLogModel.output_tokens), 0),
            sa_func.coalesce(sa_func.sum(UsageLogModel.total_tokens), 0),
            sa_func.count(UsageLogModel.id),
        )
        if since:
            query = query.where(UsageLogModel.created_at >= since)
        if until:
            query = query.where(UsageLogModel.created_at <= until)
        result = await db.execute(query)
        row = result.one()
        return int(row[0]), int(row[1]), int(row[2]), int(row[3])

    async def get_summary_by_agent(
        self, db: AsyncSession, since: datetime | None = None, until: datetime | None = None
    ) -> list[tuple[str, int, int, int, int]]:
        query = select(
            UsageLogModel.agent_id,
            sa_func.coalesce(sa_func.sum(UsageLogModel.input_tokens), 0),
            sa_func.coalesce(sa_func.sum(UsageLogModel.output_tokens), 0),
            sa_func.coalesce(sa_func.sum(UsageLogModel.total_tokens), 0),
            sa_func.count(UsageLogModel.id),
        ).group_by(UsageLogModel.agent_id)
        if since:
            query = query.where(UsageLogModel.created_at >= since)
        if until:
            query = query.where(UsageLogModel.created_at <= until)
        result = await db.execute(query)
        rows = result.all()
        return [(r.agent_id, int(r[1]), int(r[2]), int(r[3]), int(r[4])) for r in rows]

    async def get_logs(
        self, db: AsyncSession, agent_id: str | None = None,
        limit: int = 50, offset: int = 0,
    ) -> tuple[list[UsageLogModel], int]:
        query = select(UsageLogModel)
        count_query = select(sa_func.count(UsageLogModel.id))
        if agent_id:
            query = query.where(UsageLogModel.agent_id == agent_id)
            count_query = count_query.where(UsageLogModel.agent_id == agent_id)
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        query = query.order_by(UsageLogModel.created_at.desc()).limit(limit).offset(offset)
        result = await db.execute(query)
        return list(result.scalars().all()), total


usage_log_repo = UsageLogRepository()
