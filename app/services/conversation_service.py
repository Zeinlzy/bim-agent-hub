from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories import conversation_repo, message_repo
from app.models.conversation import ConversationModel, MessageModel


class ConversationService:
    async def get_or_create(
        self, session_id: uuid.UUID, agent_name: str | None, db: AsyncSession
    ) -> ConversationModel:
        conv = await conversation_repo.get_by_session_id(db, session_id)
        if conv:
            return conv
        return await conversation_repo.create(db, session_id, agent_name)

    async def add_message(
        self,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        db: AsyncSession,
        metadata: dict | None = None,
    ) -> MessageModel:
        return await message_repo.add_message(conversation_id, role, content, db, metadata=metadata)

    async def get_history(
        self, session_id: uuid.UUID, db: AsyncSession, limit: int = 50, offset: int = 0
    ) -> list[MessageModel]:
        conv = await conversation_repo.get_by_session_id(db, session_id)
        if not conv:
            return []
        return await message_repo.get_by_conversation(conv.id, db, limit=limit, offset=offset)

    async def get_conversation(
        self, session_id: uuid.UUID, db: AsyncSession
    ) -> ConversationModel | None:
        return await conversation_repo.get_by_session_id(db, session_id)

    async def get_conversation_detail(
        self, session_id: uuid.UUID, db: AsyncSession,
        message_limit: int | None = 50, message_offset: int = 0,
    ) -> tuple[ConversationModel, list[MessageModel]] | None:
        conv = await conversation_repo.get_by_session_id(db, session_id)
        if not conv:
            return None
        messages = await message_repo.get_by_conversation(
            conv.id, db, limit=message_limit, offset=message_offset
        )
        return conv, messages

    async def list_conversations(
        self, db: AsyncSession, limit: int = 50, offset: int = 0
    ) -> list[ConversationModel]:
        return await conversation_repo.list_conversations(db, limit=limit, offset=offset)

    async def delete_conversation(
        self, session_id: uuid.UUID, db: AsyncSession
    ) -> bool:
        return await conversation_repo.delete(db, session_id)


conversation_service = ConversationService()
