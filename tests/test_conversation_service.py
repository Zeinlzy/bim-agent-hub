from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.models.conversation import ConversationModel, MessageModel
from app.services.conversation_service import ConversationService


@pytest.mark.asyncio
async def test_get_or_create_creates_new():
    service = ConversationService()
    mock_db = AsyncMock()
    session_id = uuid.uuid4()

    with patch("app.services.conversation_service.conversation_repo", autospec=True) as mock_repo:
        mock_repo.get_by_session_id = AsyncMock(return_value=None)
        mock_repo.create = AsyncMock(return_value=ConversationModel(session_id=session_id, agent_name="assistant"))

        conv = await service.get_or_create(session_id, "assistant", mock_db)

        assert conv is not None
        mock_repo.get_by_session_id.assert_called_once_with(mock_db, session_id)
        mock_repo.create.assert_called_once_with(mock_db, session_id, "assistant")


@pytest.mark.asyncio
async def test_get_or_create_returns_existing():
    service = ConversationService()
    existing_conv = ConversationModel(
        session_id=uuid.uuid4(),
        agent_name="assistant",
    )
    existing_conv.id = uuid.uuid4()

    mock_db = AsyncMock()

    with patch("app.services.conversation_service.conversation_repo", autospec=True) as mock_repo:
        mock_repo.get_by_session_id = AsyncMock(return_value=existing_conv)

        conv = await service.get_or_create(existing_conv.session_id, "assistant", mock_db)

        assert conv is existing_conv
        mock_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_add_message():
    service = ConversationService()
    mock_db = AsyncMock()
    conv_id = uuid.uuid4()

    with patch("app.services.conversation_service.message_repo", autospec=True) as mock_msg_repo:
        mock_msg_repo.add_message = AsyncMock(return_value=MessageModel(
            conversation_id=conv_id, role="user", content="Hello"
        ))

        msg = await service.add_message(conv_id, "user", "Hello", mock_db)

        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.conversation_id == conv_id
        mock_msg_repo.add_message.assert_called_once_with(conv_id, "user", "Hello", mock_db, metadata=None)


@pytest.mark.asyncio
async def test_get_history_returns_messages():
    service = ConversationService()
    conv = ConversationModel(session_id=uuid.uuid4(), agent_name="test")
    conv.id = uuid.uuid4()

    mock_db = AsyncMock()

    with (
        patch("app.services.conversation_service.conversation_repo", autospec=True) as mock_conv_repo,
        patch("app.services.conversation_service.message_repo", autospec=True) as mock_msg_repo,
    ):
        mock_conv_repo.get_by_session_id = AsyncMock(return_value=conv)
        mock_msg_repo.get_by_conversation = AsyncMock(return_value=[])

        msgs = await service.get_history(conv.session_id, mock_db)

        assert msgs == []
        mock_conv_repo.get_by_session_id.assert_called_once_with(mock_db, conv.session_id)
        mock_msg_repo.get_by_conversation.assert_called_once_with(conv.id, mock_db, limit=50, offset=0)
