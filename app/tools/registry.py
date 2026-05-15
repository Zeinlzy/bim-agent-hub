from __future__ import annotations

import logging
import time
from typing import Any, Callable

from agents import function_tool
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import ToolValidationError
from app.db.repositories import tool_repo
from app.models.tool import ToolModel
from app.tools.compiler import ToolCompiler
from app.tools.validator import validate_tool_code

logger = logging.getLogger(__name__)

_BUILTIN_TOOLS: dict[str, tuple[str, str]] = {}


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Callable] = {}
        self._compiler = ToolCompiler()
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
            logger.warning("Failed to refresh tool cache, serving stale data")

    def _reset_ttl(self) -> None:
        self._last_loaded = 0.0

    async def load_from_db(self, db: AsyncSession) -> None:
        rows = await tool_repo.list_active(db)
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

            try:
                fn = self._compiler.compile_from_model(row, code=code)
                self._tools[row.name] = fn
            except Exception as e:
                logger.error("Failed to load tool '%s': %s", row.name, e)

        logger.info("Loaded %d tools from database", len(self._tools))

    def register(self, fn: Callable | None = None, name: str | None = None) -> Callable:
        if fn is None:
            return lambda f: self.register(f, name=name)
        key = name or fn.__name__
        wrapped = function_tool(fn)
        self._tools[key] = wrapped
        return wrapped

    async def register_dynamic(
        self, name: str, description: str, code: str, parameters: dict[str, Any], db: AsyncSession
    ) -> ToolModel:
        fn = self._compiler.compile(name, code)
        wrapped = function_tool(fn)
        self._tools[name] = wrapped

        existing = await tool_repo.get_by_name(db, name)
        if existing:
            existing.description = description
            existing.code = code
            existing.parameters = parameters
            existing.tool_type = "python"
            row = existing
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
        self._reset_ttl()
        return row

    def recompile_tool(self, name: str, code: str) -> None:
        fn = self._compiler.compile(name, code)
        self._tools[name] = function_tool(fn)
        self._reset_ttl()

    def remove_tool(self, name: str) -> None:
        self._tools.pop(name, None)
        self._reset_ttl()

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

    from app.db.session import get_db_session

    async with get_db_session() as db:
        for name, (desc, code) in _BUILTIN_TOOLS.items():
            existing = await tool_repo.get_by_name(db, name)
            if not existing:
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
