from __future__ import annotations

import uuid
from datetime import datetime

from agents import RunResult, RunResultStreaming, Usage
from sqlalchemy import func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.usage_log import UsageLogModel
from app.schemas.usage import UsageSummary


def _calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = settings.model_pricing.get(model)
    if not pricing:
        return 0.0
    input_cost, output_cost = pricing
    return (input_tokens / 1_000_000 * input_cost) + (output_tokens / 1_000_000 * output_cost)


class UsageService:
    async def record_run_usage(
        self,
        agent_id: str,
        result: RunResult | RunResultStreaming,
        db: AsyncSession,
        duration_ms: int | None = None,
        session_id: str | None = None,
    ) -> UsageLogModel:
        usage: Usage | None = getattr(result.context_wrapper, "usage", None)
        if not usage:
            return None

        model = result.raw_responses[0].usage.model if result.raw_responses and result.raw_responses[0].usage else ""

        log = UsageLogModel(
            session_id=uuid.UUID(session_id) if session_id else None,
            agent_id=agent_id,
            model=model or settings.openai_model,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            total_tokens=usage.total_tokens,
            cached_tokens=getattr(usage.input_tokens_details, "cached_tokens", 0) if usage.input_tokens_details else 0,
            reasoning_tokens=getattr(usage.output_tokens_details, "reasoning_tokens", 0) if usage.output_tokens_details else 0,
            requests=usage.requests,
            duration_ms=duration_ms,
        )
        db.add(log)
        await db.flush()
        return log

    async def get_summary(
        self, db: AsyncSession, since: datetime | None = None, until: datetime | None = None
    ) -> UsageSummary:
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
        total_input = row[0]
        total_output = row[1]
        total_tokens = row[2]
        count = row[3]

        return UsageSummary(
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            total_tokens=total_tokens,
            total_cost=_calculate_cost(settings.openai_model, total_input, total_output),
            run_count=count,
        )

    async def get_summary_by_agent(
        self, db: AsyncSession, since: datetime | None = None, until: datetime | None = None
    ) -> dict[str, UsageSummary]:
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
        return {
            row.agent_id: UsageSummary(
                total_input_tokens=row[1],
                total_output_tokens=row[2],
                total_tokens=row[3],
                total_cost=_calculate_cost(settings.openai_model, row[1], row[2]),
                run_count=row[4],
            )
            for row in rows
        }

    async def get_logs(
        self,
        db: AsyncSession,
        agent_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
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


usage_service = UsageService()
