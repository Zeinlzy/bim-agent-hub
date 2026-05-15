from __future__ import annotations

import uuid
from datetime import datetime

from agents import RunResult, RunResultStreaming, Usage
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.repositories import usage_log_repo
from app.models.usage_log import UsageLogModel
from app.schemas.usage import UsageSummary
from app.services.pricing import pricing_service


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

        return await usage_log_repo.create(
            db,
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

    async def get_summary(
        self, db: AsyncSession, since: datetime | None = None, until: datetime | None = None
    ) -> UsageSummary:
        total_input, total_output, total_tokens, count = await usage_log_repo.get_summary(db, since=since, until=until)
        return UsageSummary(
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            total_tokens=total_tokens,
            total_cost=pricing_service.get_cost(settings.openai_model, total_input, total_output),
            run_count=count,
        )

    async def get_summary_by_agent(
        self, db: AsyncSession, since: datetime | None = None, until: datetime | None = None
    ) -> dict[str, UsageSummary]:
        rows = await usage_log_repo.get_summary_by_agent(db, since=since, until=until)
        return {
            agent_id: UsageSummary(
                total_input_tokens=inp,
                total_output_tokens=out,
                total_tokens=total,
                total_cost=pricing_service.get_cost(settings.openai_model, inp, out),
                run_count=count,
            )
            for agent_id, inp, out, total, count in rows
        }

    async def get_logs(
        self,
        db: AsyncSession,
        agent_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[UsageLogModel], int]:
        return await usage_log_repo.get_logs(db, agent_id=agent_id, limit=limit, offset=offset)


usage_service = UsageService()
