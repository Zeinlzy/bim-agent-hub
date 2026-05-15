from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status


@pytest.mark.asyncio
async def test_chat_completions_non_streaming(client):
    with patch("app.api.chat.agent_service.run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = ("Hello! I am an assistant.", "test-session-123")
        response = await client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "Hi!"}],
                "stream": False,
                "agent_id": "assistant",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["object"] == "chat.completion"
        assert len(data["choices"]) == 1
        assert data["choices"][0]["message"]["role"] == "assistant"
        assert data["choices"][0]["message"]["content"] == "Hello! I am an assistant."
        assert data["session_id"] == "test-session-123"


@pytest.mark.asyncio
async def test_chat_completions_streaming(client):
    async def mock_stream(agent_id, messages, session_id=None):
        yield "Hello"
        yield " world!"

    with patch("app.api.chat.agent_service.run_stream", new=mock_stream):
        response = await client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "Hi!"}],
                "stream": True,
                "agent_id": "assistant",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert "text/event-stream" in response.headers["content-type"]
        body = response.text
        assert "data:" in body
        assert "[DONE]" in body
        assert "Hello" in body
        assert "world!" in body


@pytest.mark.asyncio
async def test_agent_chat_non_streaming(client):
    with patch("app.api.chat.agent_service.run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = ("Response content", "sess-456")
        response = await client.post(
            "/v1/agents/assistant/chat",
            json={
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": False,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["agent_id"] == "assistant"
        assert data["content"] == "Response content"
        assert data["session_id"] == "sess-456"


@pytest.mark.asyncio
async def test_agent_chat_streaming(client):
    async def mock_stream(agent_id, messages, session_id=None):
        yield "streaming"
        yield " response"

    with patch("app.api.chat.agent_service.run_stream", new=mock_stream):
        response = await client.post(
            "/v1/agents/assistant/chat",
            json={
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": True,
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert "text/event-stream" in response.headers["content-type"]
        body = response.text
        assert "[DONE]" in body
        assert "streaming" in body
        assert "response" in body


@pytest.mark.asyncio
async def test_chat_completions_validation_error(client):
    response = await client.post("/v1/chat/completions", json={})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
