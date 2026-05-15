from __future__ import annotations

import hashlib
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.db.session import get_db
from app.models.api_key import ApiKeyModel

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


def _generate_key() -> str:
    return f"sk-{uuid.uuid4().hex}"


@router.post("/v1/admin/api-keys", response_model=ApiKeyCreateResponse, status_code=201)
async def create_api_key(body: ApiKeyCreateRequest, db: AsyncSession = Depends(get_db)):
    plain_key = _generate_key()
    key_hash = hashlib.sha256(plain_key.encode()).hexdigest()

    row = ApiKeyModel(name=body.name, key_hash=key_hash)
    db.add(row)
    await db.flush()

    return ApiKeyCreateResponse(id=str(row.id), name=row.name, key=plain_key)


@router.get("/v1/admin/api-keys", response_model=ApiKeyListResponse)
async def list_api_keys(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ApiKeyModel).order_by(ApiKeyModel.created_at.desc())
    )
    rows = result.scalars().all()
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
    result = await db.execute(select(ApiKeyModel).where(ApiKeyModel.id == key_id))
    row = result.scalar_one_or_none()
    if not row:
        raise AppError("API key not found", status_code=404)
    row.is_active = False
    await db.flush()
