from __future__ import annotations

import pytest
from fastapi import status


@pytest.mark.asyncio
async def test_list_agents_returns_agents(client):
    response = await client.get("/v1/agents")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "agents" in data
    assert len(data["agents"]) >= 1
    assert data["agents"][0]["name"] == "assistant"


@pytest.mark.asyncio
async def test_list_agents_paginated(client):
    response = await client.get("/v1/agents?limit=1&offset=0")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["agents"]) <= 1
    assert "total" in data


@pytest.mark.skip(reason="Requires running PostgreSQL")
@pytest.mark.asyncio
async def test_get_agent_by_name(client):
    response = await client.get("/v1/agents/assistant")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "assistant"
    assert "instructions" in data


@pytest.mark.skip(reason="Requires running PostgreSQL")
@pytest.mark.asyncio
async def test_get_agent_not_found(client):
    response = await client.get("/v1/agents/nonexistent")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.skip(reason="Requires running PostgreSQL")
@pytest.mark.asyncio
async def test_delete_agent(client):
    response = await client.delete("/v1/agents/assistant")
    assert response.status_code == status.HTTP_204_NO_CONTENT
