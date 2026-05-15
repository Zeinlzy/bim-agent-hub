from __future__ import annotations

import pytest

from app.core.exceptions import ToolValidationError
from app.tools.compiler import ToolCompiler


def test_compile_valid_python_code():
    compiler = ToolCompiler()
    code = "def greet(name: str) -> str:\n    return f'Hello, {name}!'\n"
    fn = compiler.compile("greet", code, tool_type="builtin")
    assert callable(fn)
    assert fn("World") == "Hello, World!"


def test_compile_invalid_code_raises():
    compiler = ToolCompiler()
    code = "def broken(:\n    pass\n"
    with pytest.raises(ToolValidationError):
        compiler.compile("broken", code, tool_type="builtin")


def test_compile_missing_function_raises():
    compiler = ToolCompiler()
    code = "x = 1\n"
    with pytest.raises(ToolValidationError):
        compiler.compile("missing", code, tool_type="builtin")


def test_compile_disallowed_code_raises():
    compiler = ToolCompiler()
    code = "import os\ndef bad() -> str:\n    return os.getcwd()\n"
    with pytest.raises(ToolValidationError):
        compiler.compile("bad", code, tool_type="python")


def test_compile_dynamic_tool_disabled_raises():
    compiler = ToolCompiler()
    code = "def add(a: int, b: int) -> int:\n    return a + b\n"
    with pytest.raises(ToolValidationError, match="Dynamic tool execution is disabled"):
        compiler.compile("add", code, tool_type="python")


def test_exec_blocks_open():
    compiler = ToolCompiler()
    code = "def bad() -> str:\n    open('/etc/passwd')\n    return 'ok'\n"
    # Validator catches this first (Name 'open' not allowed)
    with pytest.raises(ToolValidationError, match="not allowed"):
        compiler.compile("bad", code, tool_type="builtin")


def test_exec_blocks_eval():
    compiler = ToolCompiler()
    code = "def bad() -> str:\n    return str(eval('1+1'))\n"
    with pytest.raises(ToolValidationError, match="not allowed"):
        compiler.compile("bad", code, tool_type="builtin")


def test_exec_blocks_import():
    compiler = ToolCompiler()
    code = "def bad() -> str:\n    __import__('os')\n    return 'ok'\n"
    with pytest.raises(ToolValidationError, match="not allowed"):
        compiler.compile("bad", code, tool_type="builtin")


def test_exec_without_validator_blocks_dangerous_builtins():
    from app.config import settings

    original = settings.tool_validation_enabled
    settings.tool_validation_enabled = False
    try:
        compiler = ToolCompiler()
        code = "def bad() -> str:\n    open('/etc/passwd')\n    return 'ok'\n"
        fn = compiler.compile("bad", code, tool_type="builtin")
        # The function compiles but calling it should fail since open is not in SAFE_BUILTINS
        with pytest.raises(NameError, match="open"):
            fn()
    finally:
        settings.tool_validation_enabled = original


def test_exec_allows_safe_builtins():
    compiler = ToolCompiler()
    code = "def ok() -> int:\n    return len([1, 2, 3]) + sum([4, 5])\n"
    fn = compiler.compile("ok", code, tool_type="builtin")
    assert fn() == 12


def test_exec_blocks_type_even_without_validator():
    from app.config import settings

    original = settings.tool_validation_enabled
    settings.tool_validation_enabled = False
    try:
        compiler = ToolCompiler()
        code = "def bad() -> type:\n    return type(lambda: 0)\n"
        fn = compiler.compile("bad", code, tool_type="builtin")
        with pytest.raises(NameError, match="type"):
            fn()
    finally:
        settings.tool_validation_enabled = original
