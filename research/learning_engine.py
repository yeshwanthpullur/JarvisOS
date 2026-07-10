"""Learning engine architecture."""

from __future__ import annotations

import logging

from research.learning_planner import LearningPlanner


class LearningEngine:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self.planner = LearningPlanner(logger=self._logger)
        self.initialized = False

    def initialize(self) -> None:
        self.planner.initialize()
        self.initialized = True
        self._logger.info("learning_engine_initialized")

    def build_learning_plan(self, topic: str) -> dict[str, object]:
        self._ensure_initialized()
        return self.planner.build_plan(topic)

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("LearningEngine must be initialized before use.")
