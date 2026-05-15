from __future__ import annotations

import hashlib
import hmac
import os
import uuid


def hash_api_key(key: str) -> str:
    """HMAC-SHA256 hash with a site-wide pepper for credential storage."""
    site_key = os.environ.get("SECRET_KEY", "bim-agent-hub")
    return hmac.new(site_key.encode(), key.encode(), hashlib.sha256).hexdigest()


def generate_api_key() -> tuple[str, str]:
    """Generate an API key pair.

    Returns:
        tuple[str, str]: (plain_key, key_hash) where plain_key is
        the human-usable key and key_hash is the HMAC-SHA256 digest
        for database storage.
    """
    plain = f"sk-{uuid.uuid4().hex}"
    return plain, hash_api_key(plain)
