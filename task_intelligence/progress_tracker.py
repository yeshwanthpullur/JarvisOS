"""Progress tracking for task intelligence."""

from __future__ import annotations

import logging


class ProgressTracker:
    """Track structured progress for projects and work items."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self._logger.info("progress_tracker_initialized")

    def summarize_progress(self, completed: int, total: int) -> float:
        self._ensure_initialized()
        if total <= 0:
            return 0.0
        return max(0.0, min(1.0, completed / total))

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("ProgressTracker must be initialized before use.")
