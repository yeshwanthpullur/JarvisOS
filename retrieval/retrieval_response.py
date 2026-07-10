"""Retrieval response envelope."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class RetrievalResponse:
    retrieved_items: tuple[dict[str, Any], ...] = ()
    memory_references: tuple[str, ...] = ()
    knowledge_references: tuple[str, ...] = ()
    conversation_references: tuple[str, ...] = ()
    task_references: tuple[str, ...] = ()
    workflow_references: tuple[str, ...] = ()
    confidence: float = 0.0
    statistics: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
