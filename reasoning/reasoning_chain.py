"""Reasoning chain model."""

from __future__ import annotations

from dataclasses import dataclass, field

from reasoning.reasoning_step import ReasoningStep


@dataclass(frozen=True, slots=True)
class ReasoningChain:
    steps: tuple[ReasoningStep, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)
