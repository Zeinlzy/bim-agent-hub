from __future__ import annotations

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str = "user"
    content: str


class ChatCompletionRequest(BaseModel):
    messages: list[ChatMessage]
    model: str | None = None
    stream: bool = False
    agent_id: str = "assistant"


class ChatCompletionChoice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: str = "stop"


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    choices: list[ChatCompletionChoice]


class AgentChatRequest(BaseModel):
    messages: list[ChatMessage]
    stream: bool = False


class AgentChatResponse(BaseModel):
    id: str
    agent_id: str
    content: str
