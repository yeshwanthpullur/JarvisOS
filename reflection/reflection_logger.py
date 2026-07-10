"""Logging helper for reflection."""

from __future__ import annotations

import logging


class ReflectionLogger:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self.logger.info("reflection_logger_initialized")
