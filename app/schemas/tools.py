from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class ToolCreateRequest(BaseModel):
    name: str
    description: str = ""
    code: str
    parameters: dict = Field(default_factory=dict)


class ToolUpdateRequest(BaseModel):
    description: str | None = None
    code: str | None = None
    parameters: dict | None = None


class ToolInfoResponse(BaseModel):
    id: str
    name: str
    description: str
    tool_type: str
    parameters: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ToolListResponse(BaseModel):
    tools: list[ToolInfoResponse]
