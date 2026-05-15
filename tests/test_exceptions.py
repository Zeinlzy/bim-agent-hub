from __future__ import annotations

from app.core.exceptions import (
    AppError,
    AgentNotFoundError,
    ToolValidationError,
    ToolExecutionError,
    AgentExecutionError,
)


def test_app_error_defaults():
    err = AppError()
    assert err.status_code == 500
    assert err.error_code == "internal_error"
    assert err.message == "Internal server error"


def test_agent_not_found():
    err = AgentNotFoundError("Agent 'xyz' not found")
    assert err.status_code == 404
    assert err.error_code == "agent_not_found"
    assert err.message == "Agent 'xyz' not found"


def test_tool_validation_error():
    err = ToolValidationError("Module 'os' not allowed")
    assert err.status_code == 422
    assert err.error_code == "tool_validation_error"
    assert "os" in err.message


def test_tool_execution_error():
    err = ToolExecutionError("Tool timed out")
    assert err.status_code == 502
    assert err.error_code == "tool_execution_error"


def test_agent_execution_error():
    err = AgentExecutionError("Agent timed out")
    assert err.status_code == 502
    assert err.error_code == "agent_execution_error"
