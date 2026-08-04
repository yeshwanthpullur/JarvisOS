"""Structured models for image generation workflow foundations."""

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


class ImageGenerationJobStatus(StrEnum):
    PLANNED = "planned"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"
    DISABLED = "disabled"


@dataclass(frozen=True, slots=True)
class ImageGenerationRequest:
    prompt: str
    negative_prompt: str = ""
    style: str | None = None
    size: str = "1024x1024"
    provider: str | None = None
    seed: int | None = None
    count: int = 1
    dry_run: bool = False
    local_only: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass(frozen=True, slots=True)
class ImageGenerationSafetyDecision:
    allowed: bool
    category: str
    reason: str
    safe_alternative: str | None = None
    severity: str = "low"


@dataclass(frozen=True, slots=True)
class ImageProviderStatus:
    provider_name: str
    status: ProviderAvailabilityStatus
    local: bool
    model: str | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class ImageGenerationResult:
    job_id: str
    status: ImageGenerationJobStatus
    provider: str
    output_paths: tuple[str, ...] = ()
    metadata_path: str | None = None
    safety_status: str = "unknown"
    message: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    prompt_preview: str = ""
    warnings: tuple[str, ...] = ()
    error: str | None = None
    dry_run: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.status is ImageGenerationJobStatus.COMPLETED
