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
