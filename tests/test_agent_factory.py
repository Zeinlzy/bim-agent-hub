from __future__ import annotations

import pytest

from app.agents.definitions import AgentConfig
from app.agents.factory import agent_factory
from app.core.exceptions import AgentNotFoundError


def test_build_basic_agent():
    config = AgentConfig(name="test", instructions="Be helpful.")
    agent = agent_factory.build(config)
    assert agent.name == "test"
    assert agent.instructions == "Be helpful."


def test_build_with_handoffs():
    main = AgentConfig(name="main", instructions="Main agent", handoff_agents=["helper"])
    helper = AgentConfig(name="helper", instructions="Helper agent")
    agent = agent_factory.build(main, handoff_configs={"helper": helper})
    assert len(agent.handoffs) == 1
    assert agent.handoffs[0].name == "helper"


def test_build_with_missing_handoff_skips():
    config = AgentConfig(name="main", instructions="Main", handoff_agents=["missing"])
    agent = agent_factory.build(config, handoff_configs={})
    assert len(agent.handoffs) == 0


def test_build_with_extra_tools():
    config = AgentConfig(name="test", instructions="Test")
    tool1 = lambda: "ok"
    tool2 = lambda: "no"
    agent = agent_factory.build(config, extra_tools=[tool1, tool2])
    assert len(agent.tools) == 2


def test_build_none_config_raises():
    with pytest.raises(AgentNotFoundError):
        agent_factory.build(None)
