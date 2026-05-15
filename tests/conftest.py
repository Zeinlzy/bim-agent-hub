from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.agents.definitions import AgentConfig
from app.agents.registry import registry
from app.tools.registry import tool_registry


def _seed_test_data():
    registry._cache["assistant"] = AgentConfig(
        name="assistant",
        instructions="You are a helpful assistant.",
    )

    def get_current_time() -> str:
        """Get the current date and time."""
        from datetime import datetime

        return datetime.now().isoformat()

    def echo(text: str) -> str:
        """Echo the input text back."""
        return text

    for fn in [get_current_time, echo]:
        tool_registry.register(fn)


from app.main import app  # noqa: E402


@pytest.fixture
def client():
    _seed_test_data()
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")
