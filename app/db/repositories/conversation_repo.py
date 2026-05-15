from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import ConversationModel


class ConversationRepository:
    async def get_by_session_id(self, db: AsyncSession, session_id: uuid.UUID) -> ConversationModel | None:
        result = await db.execute(
            select(ConversationModel).where(ConversationModel.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, session_id: uuid.UUID, agent_name: str | None) -> ConversationModel:
        conv = ConversationModel(session_id=session_id, agent_name=agent_name)
        db.add(conv)
        await db.flush()
        return conv

    async def list_conversations(
        self, db: AsyncSession, limit: int = 50, offset: int = 0
    ) -> list[ConversationModel]:
        result = await db.execute(
            select(ConversationModel)
            .order_by(ConversationModel.updated_at.desc())
            .limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def delete(self, db: AsyncSession, session_id: uuid.UUID) -> bool:
        result = await db.execute(
            select(ConversationModel).where(ConversationModel.session_id == session_id)
        )
        conv = result.scalar_one_or_none()
        if not conv:
            return False
        await db.delete(conv)
        await db.flush()
        return True


conversation_repo = ConversationRepository()
