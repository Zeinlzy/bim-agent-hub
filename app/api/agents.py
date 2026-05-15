from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.definitions import AgentConfig
from app.agents.registry import registry
from app.core.exceptions import AgentNotFoundError
from app.db.repositories import agent_repo
from app.db.session import get_db
from app.schemas.agents import (
    AgentCreateRequest,
    AgentDetailResponse,
    AgentInfo,
    AgentListResponse,
    AgentUpdateRequest,
)

router = APIRouter()


def _to_detail_response(row) -> AgentDetailResponse:
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


@router.get("/v1/agents", response_model=AgentListResponse)
async def list_agents(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    await registry.refresh(db)
    agents = registry.list_agents()
    total = len(agents)
    paginated = agents[offset : offset + limit]
    return AgentListResponse(
        agents=[AgentInfo(**a) for a in paginated],
        total=total,
    )


@router.get("/v1/agents/{agent_id}", response_model=AgentDetailResponse)
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    await registry.refresh(db)
    row = await agent_repo.get_by_name(db, agent_id)
    if not row:
        raise AgentNotFoundError(f"Agent '{agent_id}' not found")
    return _to_detail_response(row)


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
    return _to_detail_response(row)


@router.put("/v1/agents/{agent_id}", response_model=AgentDetailResponse)
async def update_agent(
    agent_id: str, body: AgentUpdateRequest, db: AsyncSession = Depends(get_db)
):
    row = await agent_repo.get_by_name(db, agent_id)
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
    return _to_detail_response(row)


@router.delete("/v1/agents/{agent_id}", status_code=204)
async def delete_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    row = await agent_repo.get_by_name(db, agent_id)
    if not row:
        raise AgentNotFoundError(f"Agent '{agent_id}' not found")

    await agent_repo.soft_delete(db, agent_id)
    await db.flush()

    registry.invalidate(agent_id)
