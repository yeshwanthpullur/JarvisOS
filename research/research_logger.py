"""Logging helper for research intelligence."""

from __future__ import annotations

import logging


class ResearchLogger:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger("research")
