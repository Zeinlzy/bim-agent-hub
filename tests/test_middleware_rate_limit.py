from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import status


@pytest.mark.asyncio
async def test_rate_limit_redis_exception_passes_through():
    from httpx import ASGITransport, AsyncClient

    from app.main import app

    mock_redis = MagicMock()
    mock_redis.pipeline.side_effect = ConnectionError("redis down")

    app.state.redis = mock_redis
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/v1/agents")
            assert response.status_code == status.HTTP_200_OK
    finally:
        app.state.redis = None


@pytest.mark.asyncio
async def test_rate_limit_exempt_paths(client):
    response = await client.get("/v1/health")
    assert response.status_code in (200, 503)


@pytest.mark.asyncio
async def test_rate_limit_no_redis_passes_through(client):
    response = await client.get("/v1/agents")
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_rate_limit_under_threshold_passes():
    from httpx import ASGITransport, AsyncClient

    from app.main import app

    mock_pipeline = MagicMock()
    mock_pipeline.zadd.return_value = None
    mock_pipeline.zremrangebyscore.return_value = None
    mock_pipeline.zcard.return_value = None
    mock_pipeline.expire.return_value = None
    mock_pipeline.execute = AsyncMock(return_value=[1, 0, 5, True])

    mock_redis = MagicMock()
    mock_redis.pipeline.return_value = mock_pipeline

    app.state.redis = mock_redis
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/v1/agents")
            assert response.status_code == status.HTTP_200_OK
    finally:
        app.state.redis = None


@pytest.mark.asyncio
async def test_rate_limit_over_threshold_returns_429():
    from httpx import ASGITransport, AsyncClient

    from app.main import app

    mock_pipeline = MagicMock()
    mock_pipeline.zadd.return_value = None
    mock_pipeline.zremrangebyscore.return_value = None
    mock_pipeline.zcard.return_value = None
    mock_pipeline.expire.return_value = None
    mock_pipeline.execute = AsyncMock(return_value=[1, 0, 100, True])

    mock_redis = MagicMock()
    mock_redis.pipeline.return_value = mock_pipeline

    app.state.redis = mock_redis
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/v1/agents")
            assert response.status_code == 429
            data = response.json()
            assert data["error"]["code"] == "rate_limit_exceeded"
    finally:
        app.state.redis = None
