"""Research planning architecture."""

from __future__ import annotations

import logging

from research.research_request import ResearchRequest


class ResearchPlanner:
    """Build structured research plans."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self._logger.info("research_planner_initialized")

    def build_plan(self, request: ResearchRequest) -> dict[str, object]:
        self._ensure_initialized()
        return {
            "topic": request.topic,
            "sources": request.sources,
            "strategy": request.strategy.value,
            "scope": "structured",
        }

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("ResearchPlanner must be initialized before use.")
