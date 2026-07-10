"""Response object for adaptive intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AdaptiveResponse:
    adaptation_report: str
    adaptation_candidates: tuple[str, ...] = ()
    confidence: float = 0.0
    estimated_improvement: float = 0.0
    estimated_risk: float = 0.0
    executive_recommendation: str = "review"
    memory_references: tuple[str, ...] = ()
    knowledge_references: tuple[str, ...] = ()
    diagnostics: dict[str, Any] = field(default_factory=dict)
    statistics: dict[str, Any] = field(default_factory=dict)
