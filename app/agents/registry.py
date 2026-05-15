from __future__ import annotations

import logging
import time
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.definitions import AgentConfig
from app.config import settings
from app.db.repositories import agent_repo
from app.models.agent import AgentModel

logger = logging.getLogger(__name__)


class AgentRegistry:
    def __init__(self):
        self._cache: dict[str, AgentConfig] = {}
        self._last_loaded: float = 0.0

    async def refresh(self, db: AsyncSession) -> None:
        try:
            if settings.cache_ttl_seconds == 0:
                await self.load_from_db(db)
                return
            if time.monotonic() - self._last_loaded < settings.cache_ttl_seconds:
                return
            await self.load_from_db(db)
            self._last_loaded = time.monotonic()
        except Exception:
            logger.warning("Failed to refresh agent cache, serving stale data")

    def _reset_ttl(self) -> None:
        self._last_loaded = 0.0

    async def load_from_db(self, db: AsyncSession) -> None:
        agents = await agent_repo.list_active(db)
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
        existing = await agent_repo.get_by_name_include_inactive(db, config.name)

        if existing and not replace:
            raise KeyError(f"Agent already registered: {config.name}")

        if existing:
            existing.instructions = config.instructions
            existing.model = config.model
            existing.handoff_agents = config.handoff_agents
            existing.metadata_ = config.metadata
            existing.is_active = True
            row = existing
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
        self._reset_ttl()
        return row

    def get_config(self, agent_id: str) -> AgentConfig | None:
        return self._cache.get(agent_id)

    def get_all_configs(self) -> dict[str, AgentConfig]:
        return dict(self._cache)

    def invalidate(self, agent_id: str) -> None:
        self._cache.pop(agent_id, None)
        self._reset_ttl()

    def list_agents(self) -> list[dict[str, Any]]:
        return [
            {"id": name, "name": cfg.name, "metadata": cfg.metadata}
            for name, cfg in self._cache.items()
        ]


registry = AgentRegistry()
