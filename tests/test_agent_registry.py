from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.agents.definitions import AgentConfig
from app.agents.registry import AgentRegistry


def test_get_config_existing():
    reg = AgentRegistry()
    reg._cache["test"] = AgentConfig(name="test", instructions="OK")
    assert reg.get_config("test") is not None
    assert reg.get_config("test").name == "test"


def test_get_config_missing():
    reg = AgentRegistry()
    assert reg.get_config("nonexistent") is None


def test_list_agents():
    reg = AgentRegistry()
    reg._cache["a"] = AgentConfig(name="a", instructions="A")
    reg._cache["b"] = AgentConfig(name="b", instructions="B")
    agents = reg.list_agents()
    assert len(agents) == 2
    names = {a["name"] for a in agents}
    assert names == {"a", "b"}


def test_get_all_configs():
    reg = AgentRegistry()
    cfg = AgentConfig(name="x", instructions="X")
    reg._cache["x"] = cfg
    result = reg.get_all_configs()
    assert result["x"] is cfg
    assert "x" in result
    result.pop("y", None)
    assert "x" in reg._cache


def test_invalidate_removes_from_cache():
    reg = AgentRegistry()
    reg._cache["x"] = AgentConfig(name="x", instructions="X")
    reg.invalidate("x")
    assert "x" not in reg._cache


def test_invalidate_missing_is_noop():
    reg = AgentRegistry()
    reg.invalidate("nonexistent")


async def test_load_from_db_populates_cache():
    from app.models.agent import AgentModel

    mock_db = AsyncMock()
    row = AgentModel(
        name="test",
        instructions="Test instructions",
        model="gpt-4o",
        handoff_agents=[],
        metadata_={},
    )

    with patch("app.agents.registry.agent_repo.list_active", new_callable=AsyncMock) as mock_repo:
        mock_repo.return_value = [row]
        reg = AgentRegistry()
        await reg.load_from_db(mock_db)
        assert "test" in reg._cache
        assert reg._cache["test"].instructions == "Test instructions"


async def test_register_new_config():
    from app.models.agent import AgentModel

    mock_db = AsyncMock()
    reg = AgentRegistry()
    config = AgentConfig(name="new-agent", instructions="New instructions")

    with patch(
        "app.agents.registry.agent_repo.get_by_name_include_inactive",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = None
        row = await reg.register(config, mock_db)
        assert row.name == "new-agent"
        assert "new-agent" in reg._cache


async def test_register_existing_raises_without_replace():
    from app.models.agent import AgentModel

    mock_db = AsyncMock()
    reg = AgentRegistry()
    config = AgentConfig(name="existing", instructions="Test")

    existing_row = AgentModel(name="existing", instructions="Old")
    with patch(
        "app.agents.registry.agent_repo.get_by_name_include_inactive",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = existing_row
        with pytest.raises(KeyError):
            await reg.register(config, mock_db)
