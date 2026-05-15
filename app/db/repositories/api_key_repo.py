from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import ApiKeyModel


class ApiKeyRepository:
    async def list_all(self, db: AsyncSession) -> list[ApiKeyModel]:
        result = await db.execute(
            select(ApiKeyModel).order_by(ApiKeyModel.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, db: AsyncSession, key_id: str) -> ApiKeyModel | None:
        result = await db.execute(select(ApiKeyModel).where(ApiKeyModel.id == key_id))
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, name: str, key_hash: str) -> ApiKeyModel:
        row = ApiKeyModel(name=name, key_hash=key_hash)
        db.add(row)
        await db.flush()
        return row

    async def soft_delete(self, db: AsyncSession, key_id: str) -> None:
        row = await self.get_by_id(db, key_id)
        if row:
            row.is_active = False


api_key_repo = ApiKeyRepository()
