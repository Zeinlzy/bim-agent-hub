from __future__ import annotations

import pytest
from fastapi import status


@pytest.mark.asyncio
async def test_health_returns_ok(client):
    response = await client.get("/v1/health")
    data = response.json()
    assert "status" in data
    assert "components" in data
    assert "database" in data["components"]


@pytest.mark.asyncio
async def test_health_response_structure(client):
    response = await client.get("/v1/health")
    data = response.json()
    assert "database" in data["components"]


@pytest.mark.asyncio
async def test_health_live_always_ok(client):
    response = await client.get("/v1/health/live")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_health_ready_includes_registry_status(client):
    response = await client.get("/v1/health/ready")
    data = response.json()
    assert "agents_loaded" in data["components"]
    assert "tools_loaded" in data["components"]
