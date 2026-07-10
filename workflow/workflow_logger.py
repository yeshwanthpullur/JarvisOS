"""Workflow logging helper."""

from __future__ import annotations

import logging


class WorkflowLogger:
    initialized = True

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger("workflow")
