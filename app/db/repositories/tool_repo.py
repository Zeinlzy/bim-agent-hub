from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tool import ToolModel


class ToolRepository:
    async def get_by_id(self, db: AsyncSession, tool_id: str) -> ToolModel | None:
        result = await db.execute(select(ToolModel).where(ToolModel.id == tool_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, db: AsyncSession, name: str) -> ToolModel | None:
        result = await db.execute(
            select(ToolModel).where(ToolModel.name == name)
        )
        return result.scalar_one_or_none()

    async def list_active(self, db: AsyncSession) -> list[ToolModel]:
        result = await db.execute(
            select(ToolModel).where(ToolModel.is_active == True)
        )
        return list(result.scalars().all())

    async def list_active_paginated(
        self, db: AsyncSession, limit: int = 100, offset: int = 0
    ) -> tuple[list[ToolModel], int]:
        count_result = await db.execute(
            select(func.count()).select_from(ToolModel).where(ToolModel.is_active == True)
        )
        total = count_result.scalar() or 0
        result = await db.execute(
            select(ToolModel)
            .where(ToolModel.is_active == True)
            .limit(limit).offset(offset)
        )
        return list(result.scalars().all()), total

    async def upsert(self, db: AsyncSession, row: ToolModel) -> ToolModel:
        db.add(row)
        await db.flush()
        return row

    async def soft_delete(self, db: AsyncSession, tool_id: str) -> None:
        result = await db.execute(select(ToolModel).where(ToolModel.id == tool_id))
        row = result.scalar_one_or_none()
        if row:
            row.is_active = False


tool_repo = ToolRepository()
