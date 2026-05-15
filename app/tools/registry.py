from __future__ import annotations

from typing import Any, Callable

from agents import function_tool


class ToolRegistry:
    """Registry for tools that agents can use.

    In-memory implementation for the advanced version.
    Future: add persistence, dynamic registration via API.
    """

    def __init__(self):
        self._tools: dict[str, Callable] = {}

    def register(self, fn: Callable | None = None, name: str | None = None) -> Callable:
        if fn is None:
            return lambda f: self.register(f, name=name)
        key = name or fn.__name__
        wrapped = function_tool(fn)
        self._tools[key] = wrapped
        return wrapped

    def get_tool(self, name: str) -> Callable | None:
        return self._tools.get(name)

    def get_all_tools(self) -> list[Callable]:
        return list(self._tools.values())

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {"name": name, "description": getattr(tool, "__doc__", "") or ""}
            for name, tool in self._tools.items()
        ]


# Default registry instance
tool_registry = ToolRegistry()


def register_default_tools() -> None:
    """Register built-in example tools."""

    @tool_registry.register
    def get_current_time() -> str:
        """Get the current date and time."""
        from datetime import datetime

        return datetime.now().isoformat()

    @tool_registry.register
    def echo(text: str) -> str:
        """Echo the input text back."""
        return text
