"""Typed personal intelligence models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> datetime:
    """Return the current UTC time."""
    return datetime.now(timezone.utc)


class PersonalClassification:
    """Personal information classifications."""

    EXPLICIT = "explicit"
    INFERRED = "inferred"
    DERIVED = "derived"
    TEMPORARY = "temporary"
    DISPUTED = "disputed"
    SUPERSEDED = "superseded"


@dataclass(frozen=True, slots=True)
class PersonalInformation:
    """Structured personal intelligence record."""

    item_id: str
    category: str
    value: str
    source_type: str
    source_reference: str | None
    confidence: float
    classification: str
    created_at: datetime
    updated_at: datetime
    last_confirmed_at: datetime | None = None
    active: bool = True
    superseded: bool = False
    superseded_by: str | None = None
    contradictions: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    memory_id: str | None = None


@dataclass(frozen=True, slots=True)
class PersonalQueryResult:
    """Result bundle for personal intelligence retrieval."""

    items: tuple[PersonalInformation, ...]
    source: str = "memory"
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
