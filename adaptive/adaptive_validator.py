"""Validation for adaptive intelligence."""

from __future__ import annotations

from adaptive.adaptive_request import AdaptiveRequest
from adaptive.adaptive_response import AdaptiveResponse


class AdaptiveValidator:
    def __init__(self) -> None:
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True

    def validate_request(self, request: AdaptiveRequest) -> bool:
        self._ensure_initialized()
        return bool(request.adaptive_id)

    def validate_response(self, response: AdaptiveResponse) -> bool:
        self._ensure_initialized()
        return bool(response.adaptation_report)

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("AdaptiveValidator must be initialized before use.")
