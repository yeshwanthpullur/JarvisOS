"""Logging helpers for provider execution."""

from __future__ import annotations

import logging


class ProviderExecutionLogger:
    """Factory for provider execution loggers."""

    initialized = True

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger("provider_execution")

    def child(self, name: str) -> logging.Logger:
        """Return a namespaced child logger."""
        return self.logger.getChild(name)
