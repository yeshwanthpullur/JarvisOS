"""Research context objects."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ResearchContext:
    research_id: str | None = None
    conversation_id: str | None = None
    workflow_id: str | None = None
    project_id: str | None = None
    goal_id: str | None = None
    topic: str = ""
    sources: tuple[str, ...] = ()
    strategy: str = "hybrid"
    priority: str = "normal"
    knowledge_references: tuple[str, ...] = ()
    memory_references: tuple[str, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)
    statistics: dict[str, object] = field(default_factory=dict)
