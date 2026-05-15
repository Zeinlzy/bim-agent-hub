from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.definitions import AgentConfig
from app.agents.registry import registry
from app.core.exceptions import AgentNotFoundError
from app.db.session import get_db
from app.models.agent import AgentModel
from app.schemas.agents import (
    AgentCreateRequest,
    AgentDetailResponse,
    AgentInfo,
    AgentListResponse,
    AgentUpdateRequest,
)

router = APIRouter()


@router.get("/v1/agents", response_model=AgentListResponse)
async def list_agents():
    agents = registry.list_agents()
    return AgentListResponse(agents=[AgentInfo(**a) for a in agents])


@router.get("/v1/agents/{agent_id}", response_model=AgentDetailResponse)
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AgentModel).where(AgentModel.name == agent_id, AgentModel.is_active == True)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise AgentNotFoundError(f"Agent '{agent_id}' not found")
    return AgentDetailResponse(
        id=str(row.id),
        name=row.name,
        instructions=row.instructions,
        model=row.model,
        handoff_agents=row.handoff_agents or [],
        metadata=row.metadata_ or {},
        is_active=row.is_active,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.post("/v1/agents", response_model=AgentDetailResponse, status_code=201)
async def create_agent(body: AgentCreateRequest, db: AsyncSession = Depends(get_db)):
    config = AgentConfig(
        name=body.name,
        instructions=body.instructions,
        model=body.model,
        handoff_agents=body.handoff_agents,
        metadata=body.metadata,
    )
    row = await registry.register(config, db=db)
    return AgentDetailResponse(
        id=str(row.id),
        name=row.name,
        instructions=row.instructions,
        model=row.model,
        handoff_agents=row.handoff_agents or [],
        metadata=row.metadata_ or {},
        is_active=row.is_active,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.put("/v1/agents/{agent_id}", response_model=AgentDetailResponse)
async def update_agent(
    agent_id: str, body: AgentUpdateRequest, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(AgentModel).where(AgentModel.name == agent_id, AgentModel.is_active == True)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise AgentNotFoundError(f"Agent '{agent_id}' not found")

    existing_config = registry.get_config(agent_id)
    if not existing_config:
        raise AgentNotFoundError(f"Agent '{agent_id}' not found in cache")

    updated = AgentConfig(
        name=row.name,
        instructions=body.instructions if body.instructions is not None else row.instructions,
        model=body.model if body.model is not None else row.model,
        handoff_agents=body.handoff_agents if body.handoff_agents is not None else (row.handoff_agents or []),
        metadata=body.metadata if body.metadata is not None else (row.metadata_ or {}),
    )
    row = await registry.register(updated, db=db, replace=True)
    return AgentDetailResponse(
        id=str(row.id),
        name=row.name,
        instructions=row.instructions,
        model=row.model,
        handoff_agents=row.handoff_agents or [],
        metadata=row.metadata_ or {},
        is_active=row.is_active,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.delete("/v1/agents/{agent_id}", status_code=204)
async def delete_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AgentModel).where(AgentModel.name == agent_id, AgentModel.is_active == True)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise AgentNotFoundError(f"Agent '{agent_id}' not found")

    row.is_active = False
    await db.flush()

    if agent_id in registry._cache:
        del registry._cache[agent_id]
