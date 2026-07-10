"""Task intelligence validation."""

from __future__ import annotations

import logging


class TaskValidator:
    """Validate structural task intelligence objects."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self._logger.info("task_validator_initialized")

    def validate_name(self, name: str) -> bool:
        self._ensure_initialized()
        return bool(name.strip())

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("TaskValidator must be initialized before use.")
