"""Shared bounded helpers for local-first planning foundations."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path, PurePath, PureWindowsPath
import re
from uuid import uuid4

MAX_TEXT = 1600
MAX_ITEMS = 24
SECRET_RE = re.compile(r"(?i)(api[_-]?key|access[_-]?token|password|authorization|credential|secret)\s*[:=]\s*\S+")


def new_id() -> str:
    return str(uuid4())


def now() -> str:
    return datetime.now(UTC).isoformat()


def bounded(value: object, limit: int = MAX_TEXT) -> str:
    text = str(value or "").strip()
    return text if len(text) <= limit else text[: limit - 3] + "..."


def safe_ref(value: object) -> str:
    text = str(value or "").strip()
    if PurePath(text).is_absolute() or PureWindowsPath(text).is_absolute():
        return Path(text).name
    return bounded(text, 240)


def contains_secret(value: object) -> bool:
    text = str(value or "")
    return bool(SECRET_RE.search(text)) or ".env" in text.lower()


def validate_text(value: str, *, required: bool = True, limit: int = MAX_TEXT) -> None:
    if required and not value.strip():
        raise ValueError("empty_text")
    if len(value) > limit or contains_secret(value):
        raise ValueError("unsafe_or_unbounded_text")


def validate_request_text(value: str, *, limit: int = MAX_TEXT) -> None:
    """Allow bounded unsafe text to reach a policy classifier without storing it."""
    if not value.strip() or len(value) > limit:
        raise ValueError("invalid_request_text")


def validate_items(values: tuple[object, ...], *, limit: int = MAX_ITEMS) -> None:
    if len(values) > limit or any(len(str(item)) > MAX_TEXT or contains_secret(item) for item in values):
        raise ValueError("unbounded_items")
