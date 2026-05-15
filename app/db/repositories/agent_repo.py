from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import AgentModel


class AgentRepository:
    async def get_by_name(self, db: AsyncSession, name: str) -> AgentModel | None:
        result = await db.execute(
            select(AgentModel).where(AgentModel.name == name, AgentModel.is_active == True)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, db: AsyncSession, agent_id: str) -> AgentModel | None:
        result = await db.execute(
            select(AgentModel).where(AgentModel.id == agent_id, AgentModel.is_active == True)
        )
        return result.scalar_one_or_none()

    async def list_active(self, db: AsyncSession) -> list[AgentModel]:
        result = await db.execute(
            select(AgentModel).where(AgentModel.is_active == True)
        )
        return list(result.scalars().all())

    async def get_by_name_include_inactive(self, db: AsyncSession, name: str) -> AgentModel | None:
        result = await db.execute(
            select(AgentModel).where(AgentModel.name == name)
        )
        return result.scalar_one_or_none()

    async def soft_delete(self, db: AsyncSession, name: str) -> None:
        result = await db.execute(
            select(AgentModel).where(AgentModel.name == name, AgentModel.is_active == True)
        )
        row = result.scalar_one_or_none()
        if row:
            row.is_active = False


agent_repo = AgentRepository()
