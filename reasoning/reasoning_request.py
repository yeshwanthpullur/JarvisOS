"""Reasoning request model."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ReasoningRequest:
    request_id: str
    content: str
    context: dict[str, object] = field(default_factory=dict)
