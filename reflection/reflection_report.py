"""Structured reflection report."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ReflectionReport:
    summary: str
    success_factors: tuple[str, ...] = ()
    failure_factors: tuple[str, ...] = ()
    missing_information: tuple[str, ...] = ()
    wrong_assumptions: tuple[str, ...] = ()
    improvement_opportunities: tuple[str, ...] = ()
    statistics: dict[str, Any] = field(default_factory=dict)
    diagnostics: dict[str, Any] = field(default_factory=dict)
