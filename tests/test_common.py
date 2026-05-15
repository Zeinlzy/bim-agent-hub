from __future__ import annotations

from app.common.keygen import generate_api_key, hash_api_key
from app.common.datetime_ import isoformat


def test_generate_api_key_format():
    plain, key_hash = generate_api_key()
    assert plain.startswith("sk-")
    assert len(plain) == 35  # sk- + 32 hex chars
    assert isinstance(key_hash, str)
    assert len(key_hash) == 64  # SHA-256 hex digest


def test_generate_api_key_unique():
    keys = {generate_api_key() for _ in range(10)}
    assert len(keys) == 10


def test_hash_api_key_deterministic():
    h1 = hash_api_key("test-key")
    h2 = hash_api_key("test-key")
    assert h1 == h2


def test_hash_api_key_different_for_different_keys():
    h1 = hash_api_key("key-a")
    h2 = hash_api_key("key-b")
    assert h1 != h2


def test_isoformat_returns_string():
    from datetime import datetime
    result = isoformat(datetime(2026, 5, 15, 12, 0, 0))
    assert result == "2026-05-15T12:00:00"


def test_isoformat_none_returns_none():
    assert isoformat(None) is None
