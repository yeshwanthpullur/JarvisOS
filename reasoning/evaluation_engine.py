"""Plan evaluation."""

from __future__ import annotations

import logging


class EvaluationEngine:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self._logger.info("evaluation_engine_initialized")

    def evaluate(self, options: tuple[str, ...]) -> dict[str, float]:
        self._ensure_initialized()
        return {option: 1.0 / (index + 1) for index, option in enumerate(options)}

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("EvaluationEngine must be initialized before use.")
