from __future__ import annotations

from pydantic import BaseModel, Field


class AgentInfo(BaseModel):
    id: str
    name: str
    metadata: dict = Field(default_factory=dict)


class AgentListResponse(BaseModel):
    agents: list[AgentInfo]
