from __future__ import annotations

from agents import Agent as OpenAIAgent

from app.agents.definitions import AgentConfig
from app.config import settings


class AgentRegistry:
    """Registry that holds agent configurations and creates SDK agent instances."""

    def __init__(self):
        self._configs: dict[str, AgentConfig] = {}

    def register(self, config: AgentConfig, replace: bool = False) -> None:
        if config.name in self._configs and not replace:
            raise KeyError(f"Agent already registered: {config.name}")
        self._configs[config.name] = config

    def get_config(self, agent_id: str) -> AgentConfig | None:
        return self._configs.get(agent_id)

    def list_agents(self) -> list[dict]:
        return [
            {"id": name, "name": cfg.name, "metadata": cfg.metadata}
            for name, cfg in self._configs.items()
        ]

    def build_agent(
        self, agent_id: str, extra_tools: list | None = None
    ) -> OpenAIAgent:
        config = self._configs.get(agent_id)
        if not config:
            raise ValueError(f"Unknown agent: {agent_id}")

        handoffs: list[OpenAIAgent] = []
        for name in config.handoff_agents:
            handoff_config = self._configs.get(name)
            if handoff_config:
                handoffs.append(
                    OpenAIAgent(
                        name=handoff_config.name,
                        instructions=handoff_config.instructions,
                        model=handoff_config.model or settings.openai_model,
                    )
                )

        tools = list(config.tools or [])
        if extra_tools:
            tools.extend(extra_tools)

        return OpenAIAgent(
            name=config.name,
            instructions=config.instructions,
            model=config.model or settings.openai_model,
            tools=tools or None,
            handoffs=handoffs or None,
        )


# Default registry instance
registry = AgentRegistry()


def register_default_agents() -> None:
    """Register built-in agents at startup."""
    registry.register(
        AgentConfig(
            name="assistant",
            instructions="You are a helpful assistant.",
        )
    )
