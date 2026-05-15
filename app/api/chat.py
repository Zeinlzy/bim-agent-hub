from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, HTTPException
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

    try:
        if body.stream:
            return _stream_response(agent_id, messages)
        content = await agent_service.run(agent_id, messages)
        return ChatCompletionResponse(
            id=uuid.uuid4().hex,
            choices=[
                ChatCompletionChoice(
                    message=ChatMessage(role="assistant", content=content)
                )
            ],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v1/agents/{agent_id}/chat")
async def agent_chat(agent_id: str, body: AgentChatRequest):
    messages = [m.model_dump() for m in body.messages]

    try:
        if body.stream:
            return _stream_response(agent_id, messages)
        content = await agent_service.run(agent_id, messages)
        return AgentChatResponse(
            id=uuid.uuid4().hex,
            agent_id=agent_id,
            content=content,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _stream_response(agent_id: str, messages: list[dict]):
    """Return a StreamingResponse that yields SSE-encoded chunks."""

    async def event_stream():
        async for delta in agent_service.run_stream(agent_id, messages):
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
