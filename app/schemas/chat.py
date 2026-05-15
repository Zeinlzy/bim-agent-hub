from __future__ import annotations

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field("user", max_length=20)
    content: str = Field(..., max_length=100000)


class ChatCompletionRequest(BaseModel):
    messages: list[ChatMessage]
    model: str | None = None
    stream: bool = False
    agent_id: str = "assistant"
    session_id: str | None = None


class ChatCompletionChoice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: str = "stop"


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    choices: list[ChatCompletionChoice]
    session_id: str | None = None


class AgentChatRequest(BaseModel):
    messages: list[ChatMessage]
    stream: bool = False
    session_id: str | None = None


class AgentChatResponse(BaseModel):
    id: str
    agent_id: str
    content: str
    session_id: str | None = None
