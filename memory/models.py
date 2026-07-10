"""Typed models for the JARVIS OS memory engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> datetime:
    """Return the current UTC time."""
    return datetime.now(timezone.utc)


def datetime_to_text(value: datetime) -> str:
    """Serialize a datetime for SQLite storage."""
    return value.astimezone(timezone.utc).isoformat()


def datetime_from_text(value: str) -> datetime:
    """Deserialize a datetime from SQLite storage."""
    return datetime.fromisoformat(value)


@dataclass(frozen=True, slots=True)
class Memory:
    """Persistent structured memory record."""

    id: str
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    source: str
    importance: int
    tags: tuple[str, ...] = ()
    project: str | None = None
    session_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MemoryCreate:
    """Data required to create a memory."""

    title: str
    content: str
    source: str = "manual"
    importance: int = 1
    tags: tuple[str, ...] = ()
    project: str | None = None
    session_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MemoryUpdate:
    """Optional fields that can be updated on a memory."""

    title: str | None = None
    content: str | None = None
    source: str | None = None
    importance: int | None = None
    tags: tuple[str, ...] | None = None
    project: str | None = None
    session_id: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class MemorySearchQuery:
    """Text search options for structured memory."""

    query: str
    tags: tuple[str, ...] = ()
    project: str | None = None
    session_id: str | None = None
    limit: int = 20


@dataclass(frozen=True, slots=True)
class MemoryStatistics:
    """Operational statistics for the memory database."""

    total_memories: int
    total_sessions: int
    database_size_bytes: int
    database_path: Path

