"""Learning planning architecture."""

from __future__ import annotations

import logging


class LearningPlanner:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self._logger.info("learning_planner_initialized")

    def build_plan(self, topic: str) -> dict[str, object]:
        self._ensure_initialized()
        return {"topic": topic, "objectives": (), "sequence": (), "difficulty": "normal"}

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("LearningPlanner must be initialized before use.")
