"""Reasoning step model."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ReasoningStep:
    name: str
    description: str
    metadata: dict[str, object] = field(default_factory=dict)
