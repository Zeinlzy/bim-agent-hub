from __future__ import annotations

import logging

from sqlalchemy import select

from app.config import settings
from app.models.agent import AgentModel

logger = logging.getLogger(__name__)


async def seed_default_agents() -> None:
    from app.db.repositories import agent_repo
    from app.db.session import get_db_session

    async with get_db_session() as db:
        existing = await agent_repo.get_by_name_include_inactive(db, "assistant")
        if not existing:
            db.add(
                AgentModel(
                    name="assistant",
                    instructions="You are a helpful assistant.",
                    model=settings.openai_model,
                )
            )
            await db.flush()
            logger.info("Seeded default agent: assistant")

        from app.agents.registry import registry
        await registry.load_from_db(db)
