from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConversationNotFoundError
from app.db.session import get_db
from app.schemas.conversations import (
    ConversationDetailResponse,
    ConversationInfo,
    ConversationListResponse,
    MessageInfo,
    MessageListResponse,
)
from app.services.conversation_service import conversation_service

router = APIRouter()


@router.get("/v1/conversations", response_model=ConversationListResponse)
async def list_conversations(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    convs = await conversation_service.list_conversations(db, limit=limit, offset=offset)
    return ConversationListResponse(
        conversations=[
            ConversationInfo(
                id=str(c.id),
                agent_name=c.agent_name,
                session_id=str(c.session_id),
                metadata=c.metadata_ or {},
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in convs
        ]
    )


@router.get("/v1/conversations/{session_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    message_limit: int = Query(50, ge=1, le=200),
    message_offset: int = Query(0, ge=0),
):
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        raise ConversationNotFoundError(f"Conversation '{session_id}' not found")
    result = await conversation_service.get_conversation_detail(
        sid, db, message_limit=message_limit, message_offset=message_offset
    )
    if not result:
        raise ConversationNotFoundError(f"Conversation '{session_id}' not found")

    conv, messages = result
    return ConversationDetailResponse(
        id=str(conv.id),
        agent_name=conv.agent_name,
        session_id=str(conv.session_id),
        metadata=conv.metadata_ or {},
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=[
            MessageInfo(
                id=str(m.id),
                role=m.role,
                content=m.content,
                metadata=m.metadata_ or {},
                created_at=m.created_at,
            )
            for m in messages
        ],
    )


@router.get(
    "/v1/conversations/{session_id}/messages", response_model=MessageListResponse
)
async def get_messages(
    session_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        raise ConversationNotFoundError(f"Conversation '{session_id}' not found")
    msgs = await conversation_service.get_history(sid, db, limit=limit, offset=offset)
    return MessageListResponse(
        messages=[
            MessageInfo(
                id=str(m.id),
                role=m.role,
                content=m.content,
                metadata=m.metadata_ or {},
                created_at=m.created_at,
            )
            for m in msgs
        ]
    )


@router.delete("/v1/conversations/{session_id}", status_code=204)
async def delete_conversation(session_id: str, db: AsyncSession = Depends(get_db)):
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        raise ConversationNotFoundError(f"Conversation '{session_id}' not found")
    deleted = await conversation_service.delete_conversation(sid, db)
    if not deleted:
        raise ConversationNotFoundError(f"Conversation '{session_id}' not found")
