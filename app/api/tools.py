from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ToolNotFoundError
from app.db.repositories import tool_repo
from app.db.session import get_db
from app.models.tool import ToolModel
from app.schemas.tools import ToolCreateRequest, ToolInfoResponse, ToolListResponse, ToolUpdateRequest
from app.tools.registry import tool_registry

router = APIRouter()


async def _get_active_tool_or_404(tool_id: str, db: AsyncSession) -> ToolModel:
    row = await tool_repo.get_by_id(db, tool_id)
    if not row or not row.is_active:
        raise ToolNotFoundError(f"Tool '{tool_id}' not found")
    return row


def _to_response(row: ToolModel) -> ToolInfoResponse:
    return ToolInfoResponse(
        id=str(row.id),
        name=row.name,
        description=row.description,
        tool_type=row.tool_type,
        parameters=row.parameters or {},
        is_active=row.is_active,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("/v1/tools", response_model=ToolListResponse)
async def list_tools(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    await tool_registry.refresh(db)
    rows, total = await tool_repo.list_active_paginated(db, limit=limit, offset=offset)
    return ToolListResponse(tools=[_to_response(r) for r in rows], total=total)


@router.get("/v1/tools/{tool_id}", response_model=ToolInfoResponse)
async def get_tool(tool_id: str, db: AsyncSession = Depends(get_db)):
    await tool_registry.refresh(db)
    row = await _get_active_tool_or_404(tool_id, db)
    return _to_response(row)


@router.post("/v1/tools", response_model=ToolInfoResponse, status_code=201)
async def create_tool(body: ToolCreateRequest, db: AsyncSession = Depends(get_db)):
    row = await tool_registry.register_dynamic(
        name=body.name,
        description=body.description,
        code=body.code,
        parameters=body.parameters,
        db=db,
    )
    return _to_response(row)


@router.put("/v1/tools/{tool_id}", response_model=ToolInfoResponse)
async def update_tool(
    tool_id: str, body: ToolUpdateRequest, db: AsyncSession = Depends(get_db)
):
    row = await _get_active_tool_or_404(tool_id, db)

    if body.description is not None:
        row.description = body.description
    if body.code is not None:
        row.code = body.code
        try:
            tool_registry.recompile_tool(row.name, body.code)
        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=422, detail=str(e))
    if body.parameters is not None:
        row.parameters = body.parameters

    await db.flush()
    return _to_response(row)


@router.delete("/v1/tools/{tool_id}", status_code=204)
async def delete_tool(tool_id: str, db: AsyncSession = Depends(get_db)):
    row = await _get_active_tool_or_404(tool_id, db)

    await tool_repo.soft_delete(db, tool_id)
    await db.flush()

    tool_registry.remove_tool(row.name)
