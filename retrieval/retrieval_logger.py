"""Retrieval logging."""

from __future__ import annotations

import logging


class RetrievalLogger:
    initialized = True

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger("retrieval")
