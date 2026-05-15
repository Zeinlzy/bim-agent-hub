from __future__ import annotations

import pytest
from fastapi import status

pytestmark = pytest.mark.skip(reason="Requires running PostgreSQL")


@pytest.mark.asyncio
async def test_create_api_key(client):
    response = await client.post(
        "/v1/admin/api-keys", json={"name": "test-key"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "test-key"
    assert data["key"].startswith("sk-")
    assert "id" in data


@pytest.mark.asyncio
async def test_list_api_keys(client):
    await client.post("/v1/admin/api-keys", json={"name": "key-1"})
    response = await client.get("/v1/admin/api-keys")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "api_keys" in data
    assert len(data["api_keys"]) >= 1


@pytest.mark.asyncio
async def test_delete_api_key(client):
    create_resp = await client.post(
        "/v1/admin/api-keys", json={"name": "to-delete"}
    )
    key_id = create_resp.json()["id"]
    response = await client.delete(f"/v1/admin/api-keys/{key_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.asyncio
async def test_delete_api_key_not_found(client):
    response = await client.delete(
        "/v1/admin/api-keys/00000000-0000-0000-0000-000000000000"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
