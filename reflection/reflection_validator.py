"""Validation for reflection requests and responses."""

from __future__ import annotations

import logging

from reflection.reflection_request import ReflectionRequest
from reflection.reflection_response import ReflectionResponse


class ReflectionValidator:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self.logger.info("reflection_validator_initialized")

    def validate_request(self, request: ReflectionRequest) -> bool:
        self._ensure_initialized()
        return bool(request.reflection_id)

    def validate_response(self, response: ReflectionResponse) -> bool:
        self._ensure_initialized()
        return bool(response.reflection_report)

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("ReflectionValidator must be initialized before use.")
