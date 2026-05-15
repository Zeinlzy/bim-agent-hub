from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.agent_service import AgentService


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def mock_db_session(mock_db):
    @asynccontextmanager
    async def _fake_session():
        yield mock_db

    return _fake_session


@pytest.mark.asyncio
async def test_run_returns_content(mock_db, mock_db_session):
    service = AgentService()

    mock_result = MagicMock()
    mock_result.final_output = "Test response"

    with (
        patch("app.db.session.get_db_session", side_effect=mock_db_session) as _,
        patch("app.services.agent_service.registry") as mock_registry,
        patch("app.services.agent_service.agent_factory") as mock_factory,
        patch("app.services.agent_service.tool_registry") as mock_tool_registry,
        patch("app.services.agent_service.Runner") as mock_runner,
        patch("app.services.agent_service.trace"),
    ):
        mock_registry.refresh = AsyncMock()
        mock_registry.get_config.return_value = MagicMock()
        mock_registry.get_all_configs.return_value = {}
        mock_factory.build.return_value = MagicMock()
        mock_tool_registry.refresh = AsyncMock()
        mock_tool_registry.get_all_tools.return_value = []
        mock_runner.run = AsyncMock(return_value=mock_result)

        content, sid = await service.run(
            "assistant",
            [{"role": "user", "content": "Hi"}],
            session_id=None,
        )

        assert content == "Test response"
        assert sid is None


@pytest.mark.asyncio
async def test_run_passes_single_db_session_to_helpers(mock_db, mock_db_session):
    service = AgentService()

    mock_result = MagicMock()
    mock_result.final_output = "ok"

    with (
        patch("app.db.session.get_db_session", side_effect=mock_db_session) as _,
        patch("app.services.agent_service.registry") as mock_registry,
        patch("app.services.agent_service.agent_factory") as mock_factory,
        patch("app.services.agent_service.tool_registry") as mock_tool_registry,
        patch("app.services.agent_service.Runner") as mock_runner,
        patch("app.services.agent_service.trace"),
        patch.object(service, "_load_history", new_callable=AsyncMock) as mock_load,
        patch.object(service, "_record_usage", new_callable=AsyncMock) as mock_record,
        patch.object(service, "_persist_messages", new_callable=AsyncMock) as mock_persist,
    ):
        mock_registry.refresh = AsyncMock()
        mock_registry.get_config.return_value = MagicMock()
        mock_registry.get_all_configs.return_value = {}
        mock_factory.build.return_value = MagicMock()
        mock_tool_registry.refresh = AsyncMock()
        mock_tool_registry.get_all_tools.return_value = []
        mock_runner.run = AsyncMock(return_value=mock_result)
        mock_load.return_value = []

        await service.run(
            "assistant",
            [{"role": "user", "content": "Hi"}],
            session_id="sess-1",
        )

        mock_record.assert_called_once()
        mock_persist.assert_called_once()

        record_db = mock_record.call_args[0][4]
        persist_db = mock_persist.call_args[0][4]
        assert record_db is mock_db
        assert persist_db is mock_db
