from __future__ import annotations

import json
import uuid

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.chat import (
    AgentChatRequest,
    AgentChatResponse,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatMessage,
)
from app.services.agent_service import agent_service

router = APIRouter()


@router.post("/v1/chat/completions")
async def chat_completions(body: ChatCompletionRequest):
    messages = [m.model_dump() for m in body.messages]
    agent_id = body.agent_id
    session_id = body.session_id

    if body.stream:
        return _stream_response(agent_id, messages, session_id)
    content, sid = await agent_service.run(agent_id, messages, session_id=session_id)
    return ChatCompletionResponse(
        id=uuid.uuid4().hex,
        choices=[
            ChatCompletionChoice(
                message=ChatMessage(role="assistant", content=content)
            )
        ],
        session_id=sid,
    )


@router.post("/v1/agents/{agent_id}/chat")
async def agent_chat(agent_id: str, body: AgentChatRequest):
    messages = [m.model_dump() for m in body.messages]
    session_id = body.session_id

    if body.stream:
        return _stream_response(agent_id, messages, session_id)
    content, sid = await agent_service.run(agent_id, messages, session_id=session_id)
    return AgentChatResponse(
        id=uuid.uuid4().hex,
        agent_id=agent_id,
        content=content,
        session_id=sid,
    )


def _stream_response(agent_id: str, messages: list[dict], session_id: str | None = None):
    async def event_stream():
        async for delta in agent_service.run_stream(agent_id, messages, session_id=session_id):
            chunk = {
                "id": uuid.uuid4().hex,
                "object": "chat.completion.chunk",
                "choices": [{"delta": {"content": delta}, "index": 0}],
            }
            yield f"data: {json.dumps(chunk)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
