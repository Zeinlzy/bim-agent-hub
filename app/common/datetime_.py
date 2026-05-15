from __future__ import annotations

from datetime import datetime


def isoformat(dt: datetime | None) -> str | None:
    """Convert a datetime to ISO format string, returning None for None input."""
    if dt is None:
        return None
    return dt.isoformat()
