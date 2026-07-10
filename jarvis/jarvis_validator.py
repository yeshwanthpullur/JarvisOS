"""Validator for Executive JARVIS."""

from __future__ import annotations

from dataclasses import dataclass

from jarvis.jarvis_request import JarvisRequest
from jarvis.jarvis_response import JarvisResponse


@dataclass(frozen=True, slots=True)
class JarvisValidationReport:
    """Validation report."""

    valid: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


class JarvisValidator:
    """Validates executive requests, responses, and context metadata."""

    initialized = True

    def validate_request(self, request: JarvisRequest) -> JarvisValidationReport:
        """Validate request metadata."""
        if not request.content.strip():
            return JarvisValidationReport(False, ("Request content is required.",))
        return JarvisValidationReport(True)

    def validate_response(self, response: JarvisResponse) -> JarvisValidationReport:
        """Validate response metadata."""
        if not response.request_id:
            return JarvisValidationReport(False, ("Response request_id is required.",))
        return JarvisValidationReport(True)

