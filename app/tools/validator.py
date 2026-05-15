from __future__ import annotations

import ast

from app.core.exceptions import ToolValidationError

ALLOWED_NODE_TYPES = {
    ast.Module,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.Return,
    ast.Expr,
    ast.Call,
    ast.Attribute,
    ast.Subscript,
    ast.Name,
    ast.Constant,
    ast.BinOp,
    ast.UnaryOp,
    ast.BoolOp,
    ast.Compare,
    ast.If,
    ast.IfExp,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.List,
    ast.Tuple,
    ast.Dict,
    ast.Set,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Mod,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.And,
    ast.Or,
    ast.Not,
    ast.USub,
    ast.UAdd,
    ast.Assign,
    ast.AnnAssign,
    ast.AugAssign,
    ast.Pass,
    ast.Break,
    ast.Continue,
    ast.Raise,
    ast.Try,
    ast.ExceptHandler,
    ast.Import,
    ast.ImportFrom,
    ast.alias,
    ast.arguments,
    ast.arg,
    ast.keyword,
    ast.comprehension,
    ast.ListComp,
    ast.DictComp,
    ast.SetComp,
    ast.GeneratorExp,
    ast.Lambda,
    ast.Slice,
    ast.Starred,
    ast.FormattedValue,
    ast.JoinedStr,
    ast.Str,
    ast.Num,
    ast.Delete,
    ast.Index,
    ast.Load,
    ast.Store,
    ast.Del,
}

FORBIDDEN_MODULES = {
    "os",
    "subprocess",
    "sys",
    "shutil",
    "ctypes",
    "socket",
    "requests",
    "httpx",
    "http",
    "urllib",
    "pathlib",
    "shlex",
    "signal",
    "multiprocessing",
    "concurrent",
    "threading",
    "tempfile",
    "pickle",
    "shelve",
    "marshal",
    "importlib",
    "builtins",
    "code",
    "gc",
    "inspect",
    "traceback",
    "linecache",
    "_thread",
    "platform",
    "posix",
    "resource",
    "atexit",
    "imp",
    "runpy",
    "pdb",
    "bdb",
}

FORBIDDEN_NAMES = {
    "__import__",
    "eval",
    "exec",
    "compile",
    "open",
    "input",
    "breakpoint",
    "globals",
    "locals",
    "vars",
    "dir",
    "getattr",
    "setattr",
    "delattr",
    "__builtins__",
    "type",
    "object",
    "super",
    "memoryview",
}

FORBIDDEN_ATTR_PREFIXES = {
    "__class__",
    "__base__",
    "__subclasses__",
    "__mro__",
    "__globals__",
    "__code__",
    "__closure__",
    "__init__",
    "__dict__",
    "__builtins__",
    "__getattribute__",
    "__reduce__",
    "__reduce_ex__",
    "__init_subclass__",
}


def validate_tool_code(code: str, name: str) -> None:
    """Static-analysis validation of tool source code.

    Raises ToolValidationError if the code uses disallowed patterns.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise ToolValidationError(f"Syntax error in tool '{name}': {e}")

    for node in ast.walk(tree):
        node_type = type(node)
        if node_type not in ALLOWED_NODE_TYPES:
            raise ToolValidationError(
                f"Node type '{node_type.__name__}' not allowed in tool '{name}': {ast.dump(node)[:80]}"
            )

        if isinstance(node, ast.Import):
            for alias in node.names:
                base = alias.name.split(".")[0]
                if base in FORBIDDEN_MODULES:
                    raise ToolValidationError(
                        f"Module '{alias.name}' not allowed in tool '{name}'"
                    )

        if isinstance(node, ast.ImportFrom):
            if node.module:
                base = node.module.split(".")[0]
                if base in FORBIDDEN_MODULES:
                    raise ToolValidationError(
                        f"Module '{node.module}' not allowed in tool '{name}'"
                    )

        if isinstance(node, ast.Name):
            if node.id in FORBIDDEN_NAMES:
                raise ToolValidationError(
                    f"Name '{node.id}' not allowed in tool '{name}'"
                )

        if isinstance(node, ast.Attribute):
            attr = node.attr
            if attr in FORBIDDEN_ATTR_PREFIXES:
                raise ToolValidationError(
                    f"Attribute access '{attr}' not allowed in tool '{name}'"
                )
