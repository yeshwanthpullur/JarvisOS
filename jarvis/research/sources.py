"""Source policy metadata for research planning."""

from __future__ import annotations

from dataclasses import dataclass

from .models import ResearchSourceType


@dataclass(frozen=True, slots=True)
class ResearchSourcePolicy:
    allowed_sources: tuple[ResearchSourceType, ...]
    blocked_sources: tuple[ResearchSourceType, ...]


@dataclass(frozen=True, slots=True)
class ResearchSourceRequest:
    query: str
    source_type: ResearchSourceType = ResearchSourceType.UNKNOWN
    source_ref: str = ""

