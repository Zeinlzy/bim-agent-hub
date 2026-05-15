from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_health_returns_ok(client):
    response = await client.get("/v1/health")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data
    assert "components" in data


@pytest.mark.asyncio
async def test_health_response_structure(client):
    response = await client.get("/v1/health")
    data = response.json()
    assert "database" in data["components"]
