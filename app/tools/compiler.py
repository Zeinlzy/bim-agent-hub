from __future__ import annotations

from typing import Any, Callable

from agents import function_tool

from app.config import settings
from app.core.exceptions import ToolValidationError
from app.models.tool import ToolModel
from app.tools.validator import validate_tool_code


SAFE_BUILTINS: dict[str, Any] = {
    # Type-safe data constructors and operations only.
    # Intentionally excludes: type, object, super, repr, callable,
    # issubclass, isinstance — these enable class-introspection escapes.
    "abs": abs, "all": all, "any": any, "bool": bool, "bytes": bytes,
    "chr": chr, "dict": dict, "divmod": divmod,
    "enumerate": enumerate, "filter": filter, "float": float,
    "format": format, "frozenset": frozenset, "int": int,
    "iter": iter, "len": len, "list": list, "map": map,
    "max": max, "min": min, "next": next, "ord": ord,
    "pow": pow, "print": print, "range": range,
    "reversed": reversed, "round": round, "set": set,
    "slice": slice, "sorted": sorted, "str": str,
    "sum": sum, "tuple": tuple, "zip": zip,
    "Exception": Exception, "ValueError": ValueError,
    "TypeError": TypeError, "KeyError": KeyError,
    "IndexError": IndexError, "StopIteration": StopIteration,
    "True": True, "False": False, "None": None,
}


class ToolCompiler:
    """
    Compile Python tool code into callable functions.
    Handles code compilation and function_tool wrapping.
    No DB involvement.
    """

    def compile(self, name: str, code: str, tool_type: str = "python") -> Callable:
        if settings.tool_validation_enabled:
            validate_tool_code(code, name)

        return self._exec_compile(name, code, tool_type)

    def compile_from_model(self, row: ToolModel, code: str | None = None) -> Callable:
        if code is None:
            code = row.code
        name = row.name

        if row.tool_type == "python" and settings.tool_validation_enabled and code:
            validate_tool_code(code, name)

        fn = self._exec_compile(name, code or "", tool_type=row.tool_type)
        return function_tool(fn)

    def _exec_compile(self, name: str, code: str, tool_type: str = "builtin") -> Callable:
        if tool_type == "python" and not settings.tool_dynamic_exec_enabled:
            raise ToolValidationError(
                "Dynamic tool execution is disabled. "
                "Set tool_dynamic_exec_enabled=True to enable. "
                "WARNING: this runs user-submitted code via exec() in-process. "
                "It is NOT subprocess isolation."
            )
        namespace: dict[str, Any] = {"__builtins__": SAFE_BUILTINS}
        try:
            exec(code, namespace)
        except Exception as e:
            raise ToolValidationError(f"Tool '{name}' execution failed: {e}")
        fn = namespace.get(name)
        if not fn:
            raise ToolValidationError(f"Function '{name}' not found in tool code")
        return fn
