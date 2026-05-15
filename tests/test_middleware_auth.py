from __future__ import annotations

import pytest
from fastapi import status

from app.config import settings


@pytest.mark.asyncio
async def test_auth_disabled_allows_requests(client):
    original = settings.auth_enabled
    settings.auth_enabled = False
    try:
        response = await client.get("/v1/agents")
        assert response.status_code == status.HTTP_200_OK
    finally:
        settings.auth_enabled = original


@pytest.mark.asyncio
async def test_auth_enabled_rejects_missing_header(client):
    original = settings.auth_enabled
    settings.auth_enabled = True
    try:
        response = await client.get("/v1/agents")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["error"]["code"] == "authentication_failed"
    finally:
        settings.auth_enabled = original


@pytest.mark.asyncio
async def test_auth_enabled_allows_admin_key(client):
    original_auth = settings.auth_enabled
    original_key = settings.admin_api_key
    settings.auth_enabled = True
    settings.admin_api_key = "test-admin-key"
    try:
        response = await client.get(
            "/v1/agents",
            headers={"Authorization": "Bearer test-admin-key"},
        )
        assert response.status_code == status.HTTP_200_OK
    finally:
        settings.auth_enabled = original_auth
        settings.admin_api_key = original_key


@pytest.mark.asyncio
async def test_auth_exempt_paths(client):
    original = settings.auth_enabled
    settings.auth_enabled = True
    try:
        response = await client.get("/v1/health")
        assert response.status_code in (200, 503)
    finally:
        settings.auth_enabled = original


@pytest.mark.asyncio
async def test_auth_exempt_health_live(client):
    original = settings.auth_enabled
    settings.auth_enabled = True
    try:
        response = await client.get("/v1/health/live")
        assert response.status_code in (200, 503)
    finally:
        settings.auth_enabled = original
