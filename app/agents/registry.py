from __future__ import annotations

import logging
import uuid

from agents import Agent as OpenAIAgent
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.definitions import AgentConfig
from app.config import settings
from app.core.exceptions import AgentNotFoundError
from app.models.agent import AgentModel

logger = logging.getLogger(__name__)


class AgentRegistry:
    def __init__(self):
        self._cache: dict[str, AgentConfig] = {}

    async def load_from_db(self, db: AsyncSession) -> None:
        result = await db.execute(
            select(AgentModel).where(AgentModel.is_active == True)
        )
        agents = result.scalars().all()
        self._cache.clear()
        for row in agents:
            self._cache[row.name] = AgentConfig(
                name=row.name,
                instructions=row.instructions,
                model=row.model,
                handoff_agents=row.handoff_agents or [],
                metadata=row.metadata_ or {},
            )
        logger.info("Loaded %d agents from database", len(self._cache))

    async def register(
        self, config: AgentConfig, db: AsyncSession, replace: bool = False
    ) -> AgentModel:
        existing = await db.execute(
            select(AgentModel).where(AgentModel.name == config.name)
        )
        row = existing.scalar_one_or_none()

        if row and not replace:
            raise KeyError(f"Agent already registered: {config.name}")

        if row:
            row.instructions = config.instructions
            row.model = config.model
            row.handoff_agents = config.handoff_agents
            row.metadata_ = config.metadata
            row.is_active = True
        else:
            row = AgentModel(
                name=config.name,
                instructions=config.instructions,
                model=config.model,
                handoff_agents=config.handoff_agents,
                metadata_=config.metadata,
            )
            db.add(row)

        await db.flush()
        self._cache[config.name] = config
        return row

    def get_config(self, agent_id: str) -> AgentConfig | None:
        return self._cache.get(agent_id)

    def list_agents(self) -> list[dict]:
        return [
            {"id": name, "name": cfg.name, "metadata": cfg.metadata}
            for name, cfg in self._cache.items()
        ]

    def build_agent(
        self, agent_id: str, extra_tools: list | None = None
    ) -> OpenAIAgent:
        config = self._cache.get(agent_id)
        if not config:
            raise AgentNotFoundError(f"Agent '{agent_id}' not found")

        handoffs: list[OpenAIAgent] = []
        for name in config.handoff_agents:
            handoff_config = self._cache.get(name)
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


registry = AgentRegistry()


async def register_default_agents() -> None:
    from app.db.session import get_db

    async for db in get_db():
        existing = await db.execute(
            select(AgentModel).where(AgentModel.name == "assistant")
        )
        if not existing.scalar_one_or_none():
            db.add(
                AgentModel(
                    name="assistant",
                    instructions="You are a helpful assistant.",
                    model=settings.openai_model,
                )
            )
            await db.flush()
            logger.info("Seeded default agent: assistant")
        await registry.load_from_db(db)
