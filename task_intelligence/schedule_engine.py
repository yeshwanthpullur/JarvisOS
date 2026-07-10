"""Schedule engine for task intelligence."""

from __future__ import annotations

import logging


class ScheduleEngine:
    """Declare scheduling support for task intelligence."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self._logger.info("schedule_engine_initialized")

    def schedule_mode(self, recurring: bool = False, deadline_driven: bool = False) -> str:
        self._ensure_initialized()
        if recurring:
            return "recurring"
        if deadline_driven:
            return "deadline_driven"
        return "immediate"

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("ScheduleEngine must be initialized before use.")
