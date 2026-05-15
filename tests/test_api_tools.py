from __future__ import annotations

import pytest

from app.tools.registry import tool_registry


def test_tool_registry_has_default_tools():
    tools = tool_registry.list_tools()
    tool_names = {t["name"] for t in tools}
    assert "get_current_time" in tool_names
    assert "echo" in tool_names
