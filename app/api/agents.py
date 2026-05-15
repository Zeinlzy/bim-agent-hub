from __future__ import annotations

from fastapi import APIRouter

from app.agents.registry import registry
from app.schemas.agents import AgentInfo, AgentListResponse

router = APIRouter()


@router.get("/v1/agents", response_model=AgentListResponse)
async def list_agents():
    agents = registry.list_agents()
    return AgentListResponse(
        agents=[AgentInfo(**a) for a in agents]
    )
