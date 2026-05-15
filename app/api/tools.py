from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ToolNotFoundError
from app.db.session import get_db
from app.models.tool import ToolModel
from app.schemas.tools import ToolCreateRequest, ToolInfoResponse, ToolListResponse, ToolUpdateRequest
from app.tools.registry import tool_registry

router = APIRouter()


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
async def list_tools(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ToolModel).where(ToolModel.is_active == True)
    )
    rows = result.scalars().all()
    return ToolListResponse(tools=[_to_response(r) for r in rows])


@router.get("/v1/tools/{tool_id}", response_model=ToolInfoResponse)
async def get_tool(tool_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ToolModel).where(ToolModel.id == tool_id))
    row = result.scalar_one_or_none()
    if not row or not row.is_active:
        raise ToolNotFoundError(f"Tool '{tool_id}' not found")
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
    result = await db.execute(select(ToolModel).where(ToolModel.id == tool_id))
    row = result.scalar_one_or_none()
    if not row or not row.is_active:
        raise ToolNotFoundError(f"Tool '{tool_id}' not found")

    if body.description is not None:
        row.description = body.description
    if body.code is not None:
        row.code = body.code
        fn = tool_registry._compile_tool(row.name, body.code)
        tool_registry._tools[row.name] = fn
    if body.parameters is not None:
        row.parameters = body.parameters

    await db.flush()
    return _to_response(row)


@router.delete("/v1/tools/{tool_id}", status_code=204)
async def delete_tool(tool_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ToolModel).where(ToolModel.id == tool_id))
    row = result.scalar_one_or_none()
    if not row or not row.is_active:
        raise ToolNotFoundError(f"Tool '{tool_id}' not found")

    row.is_active = False
    await db.flush()

    if row.name in tool_registry._tools:
        del tool_registry._tools[row.name]
