from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class MessageInfo(BaseModel):
    id: str
    role: str
    content: str
    metadata: dict = Field(default_factory=dict)
    created_at: datetime


class ConversationInfo(BaseModel):
    id: str
    agent_name: str | None
    session_id: str
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class ConversationDetailResponse(BaseModel):
    id: str
    agent_name: str | None
    session_id: str
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    messages: list[MessageInfo] = Field(default_factory=list)


class ConversationListResponse(BaseModel):
    conversations: list[ConversationInfo]


class MessageListResponse(BaseModel):
    messages: list[MessageInfo]
