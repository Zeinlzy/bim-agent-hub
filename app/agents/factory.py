from __future__ import annotations

from agents import Agent as OpenAIAgent

from app.agents.definitions import AgentConfig
from app.config import settings
from app.core.exceptions import AgentNotFoundError


class AgentFactory:
    """
    Build OpenAI SDK Agent instances from AgentConfig.
    Handles handoff chain resolution.
    No DB or cache involvement.
    """

    def build(
        self,
        config: AgentConfig,
        handoff_configs: dict[str, AgentConfig] | None = None,
        extra_tools: list | None = None,
    ) -> OpenAIAgent:
        if not config:
            raise AgentNotFoundError("Agent config not provided")

        handoffs: list[OpenAIAgent] = []
        if handoff_configs:
            for name in config.handoff_agents:
                hc = handoff_configs.get(name)
                if hc:
                    handoffs.append(
                        OpenAIAgent(
                            name=hc.name,
                            instructions=hc.instructions,
                            model=hc.model or settings.openai_model,
                        )
                    )

        tools = list(config.tools or [])
        if extra_tools:
            tools.extend(extra_tools)

        return OpenAIAgent(
            name=config.name,
            instructions=config.instructions,
            model=config.model or settings.openai_model,
            tools=tools,
            handoffs=handoffs,
        )


agent_factory = AgentFactory()
