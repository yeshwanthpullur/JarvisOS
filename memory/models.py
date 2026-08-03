"""Typed models for the JARVIS OS memory engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
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


class MemoryType(StrEnum):
    """Logical categories for durable and temporary memories."""

    USER_PREFERENCE = "user_preference"
    USER_PROFILE = "user_profile"
    PROJECT_CONTEXT = "project_context"
    PROJECT_DECISION = "project_decision"
    GOAL_SUMMARY = "goal_summary"
    TASK_SUMMARY = "task_summary"
    CONVERSATION_SUMMARY = "conversation_summary"
    WORKFLOW_SUMMARY = "workflow_summary"
    STUDY_CONTEXT = "study_context"
    DEVICE_PREFERENCE = "device_preference"
    COMMUNICATION_PREFERENCE = "communication_preference"
    TEMPORARY_CONTEXT = "temporary_context"
    CUSTOM_NOTE = "custom_note"


class MemorySensitivity(StrEnum):
    """Sensitivity levels supported by the local policy layer."""

    PUBLIC = "public"
    NORMAL = "normal"
    PERSONAL = "personal"
    SENSITIVE = "sensitive"
    PROHIBITED = "prohibited"


class MemorySource(StrEnum):
    """Sources from which memory may originate."""

    EXPLICIT_USER = "explicit_user"
    SUGGESTED_USER = "suggested_user"
    AUTOMATIC_SESSION = "automatic_session"
    PROJECT_FILE = "project_file"
    TASK = "task"
    GOAL = "goal"
    TOOL = "tool"
    CONVERSATION = "conversation"
    IMPORT = "import"
    SYSTEM = "system"


class MemoryStatus(StrEnum):
    """Lifecycle states for local memory."""

    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"
    DELETED = "deleted"
    EXPIRED = "expired"
    PENDING_CONFIRMATION = "pending_confirmation"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class MemoryPermission:
    """Permission metadata for memory operations."""

    name: str
    allowed: bool = True
    reason: str | None = None


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
    memory_type: str = MemoryType.CUSTOM_NOTE
    sensitivity: str = MemorySensitivity.NORMAL
    status: str = MemoryStatus.ACTIVE
    confidence: float = 0.5
    last_accessed_at: datetime | None = None
    access_count: int = 0
    expiration_at: datetime | None = None
    supersedes_memory_id: str | None = None
    related_goal_id: str | None = None
    related_task_id: str | None = None
    checksum: str | None = None
    version: int = 1
    user_confirmed: bool = False
    normalized_content: str = ""


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
    memory_type: str = MemoryType.CUSTOM_NOTE
    sensitivity: str = MemorySensitivity.NORMAL
    status: str = MemoryStatus.ACTIVE
    confidence: float = 0.5
    last_accessed_at: datetime | None = None
    access_count: int = 0
    expiration_at: datetime | None = None
    supersedes_memory_id: str | None = None
    related_goal_id: str | None = None
    related_task_id: str | None = None
    checksum: str | None = None
    version: int = 1
    user_confirmed: bool = False
    normalized_content: str = ""


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
    memory_type: str | None = None
    sensitivity: str | None = None
    status: str | None = None
    confidence: float | None = None
    last_accessed_at: datetime | None = None
    access_count: int | None = None
    expiration_at: datetime | None = None
    supersedes_memory_id: str | None = None
    related_goal_id: str | None = None
    related_task_id: str | None = None
    checksum: str | None = None
    version: int | None = None
    user_confirmed: bool | None = None
    normalized_content: str | None = None


@dataclass(frozen=True, slots=True)
class MemorySearchQuery:
    """Text search options for structured memory."""

    query: str
    tags: tuple[str, ...] = ()
    project: str | None = None
    session_id: str | None = None
    memory_types: tuple[str, ...] = ()
    statuses: tuple[str, ...] = ()
    sensitivities: tuple[str, ...] = ()
    limit: int = 20


@dataclass(frozen=True, slots=True)
class MemorySummary:
    """Bounded readable summary of one or more memories."""

    title: str
    content: str
    memory_ids: tuple[str, ...] = ()
    memory_type: str = MemoryType.CUSTOM_NOTE
    confidence: float = 0.0
    tags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MemoryQuery:
    """Memory search intent with bounded context controls."""

    query: str
    project: str | None = None
    session_id: str | None = None
    memory_types: tuple[str, ...] = ()
    statuses: tuple[str, ...] = ()
    sensitivities: tuple[str, ...] = ()
    limit: int = 8
    max_context_chars: int = 6000


@dataclass(frozen=True, slots=True)
class MemorySearchResult:
    """Single ranked memory result."""

    memory: Memory
    relevance: float
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MemoryWriteRequest:
    """Policy-checked memory write request."""

    title: str
    content: str
    memory_type: str = MemoryType.CUSTOM_NOTE
    sensitivity: str = MemorySensitivity.NORMAL
    source: str = MemorySource.EXPLICIT_USER
    importance: int = 1
    tags: tuple[str, ...] = ()
    project: str | None = None
    session_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.5
    user_confirmed: bool = False


@dataclass(frozen=True, slots=True)
class MemoryUpdateRequest:
    """Policy-checked memory update request."""

    memory_id: str
    title: str | None = None
    content: str | None = None
    memory_type: str | None = None
    sensitivity: str | None = None
    status: str | None = None
    source: str | None = None
    importance: int | None = None
    tags: tuple[str, ...] | None = None
    project: str | None = None
    session_id: str | None = None
    metadata: dict[str, Any] | None = None
    confidence: float | None = None
    user_confirmed: bool | None = None


@dataclass(frozen=True, slots=True)
class MemoryDeletionRequest:
    """Memory deletion request."""

    memory_id: str
    reason: str = "user_request"


@dataclass(frozen=True, slots=True)
class MemoryConsolidationResult:
    """Result of bounded deduplication and consolidation."""

    considered: int
    updated: int
    archived: int
    deleted: int
    preview: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MemoryStatistics:
    """Operational statistics for the memory database."""

    total_memories: int
    total_sessions: int
    database_size_bytes: int
    database_path: Path
