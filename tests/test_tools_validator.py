from __future__ import annotations

import pytest

from app.tools.validator import validate_tool_code


def test_valid_simple_tool():
    code = """
def greet(name: str) -> str:
    return f"Hello, {name}!"
"""
    validate_tool_code(code, "greet")


def test_valid_math_tool():
    code = """
def add(a: int, b: int) -> int:
    return a + b
"""
    validate_tool_code(code, "add")


def test_rejects_os_import():
    code = """
import os

def bad_tool() -> str:
    return os.getcwd()
"""
    with pytest.raises(Exception) as exc:
        validate_tool_code(code, "bad_tool")
    assert "not allowed" in str(exc.value)


def test_rejects_subprocess_import():
    code = """
import subprocess

def bad_tool() -> str:
    subprocess.run(["echo", "hi"])
    return "done"
"""
    with pytest.raises(Exception) as exc:
        validate_tool_code(code, "bad_tool")
    assert "not allowed" in str(exc.value)


def test_rejects_eval():
    code = """
def bad_tool(code: str) -> str:
    return eval(code)
"""
    with pytest.raises(Exception) as exc:
        validate_tool_code(code, "bad_tool")
    assert "not allowed" in str(exc.value)


def test_rejects_syntax_error():
    code = """
def broken_tool(:
    return
"""
    with pytest.raises(Exception) as exc:
        validate_tool_code(code, "broken_tool")
    assert "Syntax error" in str(exc.value)


def test_rejects_getattr():
    code = """
def bad_tool(obj) -> str:
    return getattr(obj, "__class__")
"""
    with pytest.raises(Exception) as exc:
        validate_tool_code(code, "bad_tool")
    assert "not allowed" in str(exc.value)


def test_valid_tool_with_try_except():
    code = """
def safe_divide(a: float, b: float) -> float:
    try:
        return a / b
    except ZeroDivisionError:
        return 0.0
"""
    validate_tool_code(code, "safe_divide")


def test_valid_tool_with_list_comp():
    code = """
def double_all(items: list) -> list:
    return [x * 2 for x in items]
"""
    validate_tool_code(code, "double_all")


def test_rejects_socket_import():
    code = """
import socket

def bad_tool() -> str:
    return "evil"
"""
    with pytest.raises(Exception) as exc:
        validate_tool_code(code, "bad_tool")
    assert "not allowed" in str(exc.value)
