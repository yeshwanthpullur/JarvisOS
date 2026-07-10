"""Logging helper for task intelligence."""

from __future__ import annotations

import logging


class TaskLogger:
    """Provide a namespaced logger for task intelligence."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger("task_intelligence")
