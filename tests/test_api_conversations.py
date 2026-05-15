from __future__ import annotations

import pytest
from fastapi import status

pytestmark = pytest.mark.skip(reason="Requires running PostgreSQL")


@pytest.mark.asyncio
async def test_list_conversations(client):
    response = await client.get("/v1/conversations")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "conversations" in data


@pytest.mark.asyncio
async def test_get_conversation_not_found(client):
    response = await client.get("/v1/conversations/00000000-0000-0000-0000-000000000000")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_messages_not_found(client):
    response = await client.get("/v1/conversations/00000000-0000-0000-0000-000000000000/messages")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["messages"] == []


@pytest.mark.asyncio
async def test_delete_conversation_not_found(client):
    response = await client.delete("/v1/conversations/00000000-0000-0000-0000-000000000000")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_invalid_uuid_format_returns_404(client):
    response = await client.get("/v1/conversations/not-a-uuid")
    assert response.status_code == status.HTTP_404_NOT_FOUND
