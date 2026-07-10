"""Logging helper for adaptive intelligence."""

from __future__ import annotations

import logging


class AdaptiveLogger:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self.logger.info("adaptive_logger_initialized")
