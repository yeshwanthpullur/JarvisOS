"""Task persistence data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class TaskFile:
    """File associated with a saved task."""

    path: Path
    purpose: str
    checksum: str | None = None


@dataclass(frozen=True, slots=True)
class GeneratedCode:
    """Generated code captured as part of a task snapshot."""

    language: str
    content: str
    target_path: Path | None = None


@dataclass(frozen=True, slots=True)
class TaskSnapshot:
    """Provider-neutral persisted task state."""

    task_id: str
    goal: str
    current_progress: str
    completed_steps: tuple[str, ...]
    remaining_steps: tuple[str, ...]
    files: tuple[TaskFile, ...] = ()
    generated_code: tuple[GeneratedCode, ...] = ()
    referenced_documents: tuple[Path, ...] = ()
    current_provider: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Mapping[str, Any] = field(default_factory=dict)

