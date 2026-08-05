"""Structured models for video editing workflow foundations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class ProviderAvailabilityStatus(StrEnum):
    READY = "ready"
    UNAVAILABLE = "unavailable"
    DISABLED = "disabled"
    NOT_CONFIGURED = "not_configured"
    ERROR = "error"


class VideoEditingJobStatus(StrEnum):
    PLANNED = "planned"
    BLOCKED = "blocked"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"
    DISABLED = "disabled"


@dataclass(frozen=True, slots=True)
class VideoEditingRequest:
    prompt: str
    source_media: tuple[str, ...] = ()
    edit_style: str | None = None
    provider: str | None = None
    dry_run: bool = False
    local_only: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass(frozen=True, slots=True)
class VideoEditingSafetyDecision:
    allowed: bool
    category: str
    reason: str
    safe_alternative: str | None = None
    severity: str = "low"


@dataclass(frozen=True, slots=True)
class VideoProviderStatus:
    provider_name: str
    status: ProviderAvailabilityStatus
    local: bool
    model: str | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class VideoEditingPlan:
    plan_id: str
    status: VideoEditingJobStatus
    provider: str
    message: str = ""
    prompt_preview: str = ""
    source_media: tuple[str, ...] = ()
    plan_steps: tuple[str, ...] = ()
    deliverables: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    error: str | None = None
    dry_run: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.status is VideoEditingJobStatus.PLANNED


@dataclass(frozen=True, slots=True)
class VideoEditingResult:
    plan_id: str
    status: VideoEditingJobStatus
    provider: str
    message: str = ""
    prompt_preview: str = ""
    source_media: tuple[str, ...] = ()
    plan_steps: tuple[str, ...] = ()
    deliverables: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    error: str | None = None
    dry_run: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    metadata_path: str | None = None

    @property
    def success(self) -> bool:
        return self.status is VideoEditingJobStatus.PLANNED
