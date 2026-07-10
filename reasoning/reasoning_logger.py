"""Logging helper for reasoning."""

from __future__ import annotations

import logging


class ReasoningLogger:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger("reasoning")
