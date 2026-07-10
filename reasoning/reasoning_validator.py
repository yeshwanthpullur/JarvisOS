"""Reasoning validation."""

from __future__ import annotations

import logging

from reasoning.reasoning_request import ReasoningRequest
from reasoning.reasoning_response import ReasoningResponse


class ReasoningValidator:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self._logger.info("reasoning_validator_initialized")

    def validate_request(self, request: ReasoningRequest) -> bool:
        self._ensure_initialized()
        return bool(request.content.strip())

    def validate_response(self, response: ReasoningResponse) -> bool:
        self._ensure_initialized()
        return 0.0 <= response.confidence <= 1.0

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("ReasoningValidator must be initialized before use.")
