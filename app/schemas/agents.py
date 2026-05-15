from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class AgentInfo(BaseModel):
    id: str
    name: str
    metadata: dict = Field(default_factory=dict)


class AgentListResponse(BaseModel):
    agents: list[AgentInfo]


class AgentCreateRequest(BaseModel):
    name: str
    instructions: str
    model: str | None = None
    handoff_agents: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class AgentUpdateRequest(BaseModel):
    instructions: str | None = None
    model: str | None = None
    handoff_agents: list[str] | None = None
    metadata: dict | None = None


class AgentDetailResponse(BaseModel):
    id: str
    name: str
    instructions: str
    model: str | None
    handoff_agents: list[str]
    metadata: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime
