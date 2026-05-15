from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import MessageModel


class MessageRepository:
    async def get_by_conversation(
        self, conversation_id: uuid.UUID, db: AsyncSession,
        limit: int | None = None, offset: int = 0,
    ) -> list[MessageModel]:
        query = (
            select(MessageModel)
            .where(MessageModel.conversation_id == conversation_id)
            .order_by(MessageModel.created_at.asc())
        )
        if limit is not None:
            query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def add_message(
        self, conversation_id: uuid.UUID, role: str, content: str,
        db: AsyncSession, metadata: dict | None = None,
    ) -> MessageModel:
        msg = MessageModel(
            conversation_id=conversation_id, role=role,
            content=content, metadata_=metadata or {},
        )
        db.add(msg)
        await db.flush()
        return msg


message_repo = MessageRepository()
