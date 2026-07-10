"""Shared utilities for Agent Creator modules."""

from __future__ import annotations

import re
from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def normalize_identifier(value: str) -> str:
    """Normalize a name into a deterministic identifier."""
    normalized = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip().lower()).strip("_")
    return normalized or "unnamed"


def class_name_from_identifier(identifier: str) -> str:
    """Return a Python class name for an identifier."""
    return "".join(part.capitalize() for part in normalize_identifier(identifier).split("_")) + "Agent"

