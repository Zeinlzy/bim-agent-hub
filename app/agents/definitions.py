from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class AgentConfig:
    name: str
    instructions: str
    model: str | None = None
    tools: list[Callable] = field(default_factory=list)
    handoff_agents: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
