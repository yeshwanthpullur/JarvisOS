"""Retrieval request envelope."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from retrieval.retrieval_strategy import RetrievalStrategy


@dataclass(frozen=True, slots=True)
class RetrievalRequest:
    request_id: str = field(default_factory=lambda: str(uuid4()))
    conversation_id: str | None = None
    workflow_id: str | None = None
    intent: str = ""
    goal: str = ""
    query: str = ""
    required_sources: tuple[str, ...] = ()
    retrieval_strategy: RetrievalStrategy = RetrievalStrategy.HYBRID
    context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
