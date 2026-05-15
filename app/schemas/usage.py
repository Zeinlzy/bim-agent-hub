from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class UsageLogInfo(BaseModel):
    id: str
    session_id: str | None
    agent_id: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cached_tokens: int
    reasoning_tokens: int
    duration_ms: int | None
    created_at: datetime


class UsageSummary(BaseModel):
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    run_count: int = 0

    @classmethod
    def empty(cls) -> UsageSummary:
        return cls()


class UsageStatsResponse(BaseModel):
    total: UsageSummary
    by_agent: dict[str, UsageSummary] = Field(default_factory=dict)


class UsageLogListResponse(BaseModel):
    logs: list[UsageLogInfo]
    total: int = 0
