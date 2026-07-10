"""Templates for task intelligence."""

from __future__ import annotations

import logging


class TaskTemplates:
    """Template registry placeholder for task intelligence."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self._logger.info("task_templates_initialized")

    def list_templates(self) -> tuple[str, ...]:
        self._ensure_initialized()
        return ()

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("TaskTemplates must be initialized before use.")
