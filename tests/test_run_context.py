from __future__ import annotations

from app.services.run_context import AgentRunContext


def test_run_context_defaults():
    ctx = AgentRunContext(agent_id="test-agent")
    assert ctx.agent_id == "test-agent"
    assert ctx.max_turns == 25
    assert ctx.timeout_seconds == 120
    assert ctx.session_id is None


def test_run_context_custom_values():
    ctx = AgentRunContext(
        agent_id="custom-agent",
        max_turns=50,
        timeout_seconds=60,
        session_id="abc-123",
    )
    assert ctx.agent_id == "custom-agent"
    assert ctx.max_turns == 50
    assert ctx.timeout_seconds == 60
    assert ctx.session_id == "abc-123"


def test_run_context_elapsed_ms():
    ctx = AgentRunContext(agent_id="test")
    assert ctx.elapsed_ms is None
    ctx.start()
    assert ctx.elapsed_ms is not None
    assert ctx.elapsed_ms >= 0


def test_run_context_builds_run_config():
    ctx = AgentRunContext(
        agent_id="test-agent",
        session_id="session-123",
    )
    run_config = ctx.build_run_config()
    assert run_config.workflow_name == "test-agent"
    assert run_config.trace_metadata["agent_id"] == "test-agent"
    assert run_config.trace_metadata["session_id"] == "session-123"
