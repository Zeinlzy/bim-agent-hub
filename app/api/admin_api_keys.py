from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.keygen import generate_api_key
from app.core.exceptions import ApiKeyNotFoundError
from app.db.repositories import api_key_repo
from app.db.session import get_db

router = APIRouter()


class ApiKeyCreateRequest(BaseModel):
    name: str


class ApiKeyCreateResponse(BaseModel):
    id: str
    name: str
    key: str


class ApiKeyInfo(BaseModel):
    id: str
    name: str
    is_active: bool
    created_at: str | None = None


class ApiKeyListResponse(BaseModel):
    api_keys: list[ApiKeyInfo]


@router.post("/v1/admin/api-keys", response_model=ApiKeyCreateResponse, status_code=201)
async def create_api_key(body: ApiKeyCreateRequest, db: AsyncSession = Depends(get_db)):
    plain_key, key_hash = generate_api_key()
    row = await api_key_repo.create(db, name=body.name, key_hash=key_hash)
    return ApiKeyCreateResponse(id=str(row.id), name=row.name, key=plain_key)


@router.get("/v1/admin/api-keys", response_model=ApiKeyListResponse)
async def list_api_keys(db: AsyncSession = Depends(get_db)):
    rows = await api_key_repo.list_all(db)
    return ApiKeyListResponse(
        api_keys=[
            ApiKeyInfo(
                id=str(r.id),
                name=r.name,
                is_active=r.is_active,
                created_at=r.created_at.isoformat() if r.created_at else None,
            )
            for r in rows
        ]
    )


@router.delete("/v1/admin/api-keys/{key_id}", status_code=204)
async def delete_api_key(key_id: str, db: AsyncSession = Depends(get_db)):
    row = await api_key_repo.get_by_id(db, key_id)
    if not row:
        raise ApiKeyNotFoundError("API key not found")
    row.is_active = False
    await db.flush()
