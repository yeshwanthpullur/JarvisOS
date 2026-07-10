"""Research response objects."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ResearchResponse:
    findings: tuple[str, ...] = ()
    summary: str = ""
    references: tuple[str, ...] = ()
    learning_plan: dict[str, object] = field(default_factory=dict)
    confidence: float = 0.0
    metadata: dict[str, object] = field(default_factory=dict)
