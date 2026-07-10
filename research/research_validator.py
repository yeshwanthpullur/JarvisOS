"""Research validation architecture."""

from __future__ import annotations

import logging

from research.research_request import ResearchRequest


class ResearchValidator:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self._logger.info("research_validator_initialized")

    def validate_request(self, request: ResearchRequest) -> bool:
        self._ensure_initialized()
        return bool(request.topic.strip())

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("ResearchValidator must be initialized before use.")
