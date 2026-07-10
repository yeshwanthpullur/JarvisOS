"""Research request objects."""

from __future__ import annotations

from dataclasses import dataclass, field

from research.research_strategy import ResearchStrategy


@dataclass(slots=True)
class ResearchRequest:
    request_id: str
    topic: str
    strategy: ResearchStrategy = ResearchStrategy.HYBRID
    sources: tuple[str, ...] = ()
    context: dict[str, object] = field(default_factory=dict)
    metadata: dict[str, object] = field(default_factory=dict)
