from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import ConversationModel, MessageModel


class ConversationService:
    async def get_or_create(
        self, session_id: uuid.UUID, agent_name: str | None, db: AsyncSession
    ) -> ConversationModel:
        result = await db.execute(
            select(ConversationModel).where(ConversationModel.session_id == session_id)
        )
        conv = result.scalar_one_or_none()
        if conv:
            return conv

        conv = ConversationModel(
            session_id=session_id,
            agent_name=agent_name,
        )
        db.add(conv)
        await db.flush()
        return conv

    async def add_message(
        self,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        db: AsyncSession,
        metadata: dict | None = None,
    ) -> MessageModel:
        msg = MessageModel(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata_=metadata or {},
        )
        db.add(msg)
        await db.flush()
        return msg

    async def get_history(
        self, session_id: uuid.UUID, db: AsyncSession, limit: int = 50, offset: int = 0
    ) -> list[MessageModel]:
        result = await db.execute(
            select(ConversationModel).where(ConversationModel.session_id == session_id)
        )
        conv = result.scalar_one_or_none()
        if not conv:
            return []

        result = await db.execute(
            select(MessageModel)
            .where(MessageModel.conversation_id == conv.id)
            .order_by(MessageModel.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_conversation(
        self, session_id: uuid.UUID, db: AsyncSession
    ) -> ConversationModel | None:
        result = await db.execute(
            select(ConversationModel).where(ConversationModel.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def list_conversations(
        self, db: AsyncSession, limit: int = 50, offset: int = 0
    ) -> list[ConversationModel]:
        result = await db.execute(
            select(ConversationModel)
            .order_by(ConversationModel.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def delete_conversation(
        self, session_id: uuid.UUID, db: AsyncSession
    ) -> bool:
        result = await db.execute(
            select(ConversationModel).where(ConversationModel.session_id == session_id)
        )
        conv = result.scalar_one_or_none()
        if not conv:
            return False
        await db.delete(conv)
        await db.flush()
        return True


conversation_service = ConversationService()
