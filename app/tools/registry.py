from __future__ import annotations

import logging
from typing import Any, Callable

from agents import function_tool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import ToolValidationError
from app.models.tool import ToolModel
from app.tools.sandbox import validate_tool_code

logger = logging.getLogger(__name__)

_BUILTIN_TOOLS: dict[str, tuple[str, str]] = {}


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Callable] = {}

    async def load_from_db(self, db: AsyncSession) -> None:
        result = await db.execute(
            select(ToolModel).where(ToolModel.is_active == True)
        )
        rows = result.scalars().all()
        self._tools.clear()

        for row in rows:
            if row.tool_type == "builtin":
                code = _BUILTIN_TOOLS.get(row.name, ("", ""))[1]
                if not code:
                    continue
            else:
                code = row.code

            if not code:
                continue

            if row.tool_type == "python" and settings.tool_validation_enabled:
                try:
                    validate_tool_code(code, row.name)
                except ToolValidationError as e:
                    logger.error("Skipping invalid tool '%s': %s", row.name, e)
                    continue

            try:
                fn = self._compile_tool(row.name, code)
                wrapped = function_tool(fn)
                self._tools[row.name] = wrapped
            except Exception as e:
                logger.error("Failed to load tool '%s': %s", row.name, e)

        logger.info("Loaded %d tools from database", len(self._tools))

    def _compile_tool(self, name: str, code: str) -> Callable:
        namespace: dict[str, Any] = {"__builtins__": {}}
        exec(code, namespace)
        fn = namespace.get(name)
        if not fn:
            raise ValueError(f"Function '{name}' not found in tool code")
        return fn

    def register(self, fn: Callable | None = None, name: str | None = None) -> Callable:
        if fn is None:
            return lambda f: self.register(f, name=name)
        key = name or fn.__name__
        wrapped = function_tool(fn)
        self._tools[key] = wrapped
        return wrapped

    async def register_dynamic(
        self, name: str, description: str, code: str, parameters: dict, db: AsyncSession
    ) -> ToolModel:
        if settings.tool_validation_enabled:
            validate_tool_code(code, name)
        fn = self._compile_tool(name, code)
        wrapped = function_tool(fn)
        self._tools[name] = wrapped

        existing = await db.execute(
            select(ToolModel).where(ToolModel.name == name)
        )
        row = existing.scalar_one_or_none()
        if row:
            row.description = description
            row.code = code
            row.parameters = parameters
            row.tool_type = "python"
        else:
            row = ToolModel(
                name=name,
                description=description,
                code=code,
                parameters=parameters,
                tool_type="python",
            )
            db.add(row)
        await db.flush()
        return row

    def get_tool(self, name: str) -> Callable | None:
        return self._tools.get(name)

    def get_all_tools(self) -> list[Callable]:
        return list(self._tools.values())

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {"name": name, "description": getattr(tool, "__doc__", "") or ""}
            for name, tool in self._tools.items()
        ]


tool_registry = ToolRegistry()


async def register_default_tools() -> None:
    import inspect

    def get_current_time() -> str:
        """Get the current date and time."""
        from datetime import datetime
        return datetime.now().isoformat()

    def echo(text: str) -> str:
        """Echo the input text back."""
        return text

    for fn in [get_current_time, echo]:
        _BUILTIN_TOOLS[fn.__name__] = (fn.__doc__ or "", inspect.getsource(fn))
        tool_registry.register(fn)

    from app.db.session import get_db

    async for db in get_db():
        for name, (desc, code) in _BUILTIN_TOOLS.items():
            existing = await db.execute(
                select(ToolModel).where(ToolModel.name == name)
            )
            if not existing.scalar_one_or_none():
                db.add(
                    ToolModel(
                        name=name,
                        description=desc,
                        tool_type="builtin",
                        code=code,
                    )
                )
        await db.flush()
        await tool_registry.load_from_db(db)
