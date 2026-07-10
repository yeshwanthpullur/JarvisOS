"""Validation helpers for provider execution objects."""

from __future__ import annotations

from provider_execution.execution_request import ProviderExecutionRequest
from provider_execution.execution_response import ProviderExecutionResponse
from provider_execution.provider_registry import ProviderExecutionRecord


class ProviderExecutionValidator:
    """Validates execution requests, responses, and records."""

    initialized = True

    def validate_request(self, request: ProviderExecutionRequest) -> tuple[bool, tuple[str, ...]]:
        """Validate a provider execution request."""
        issues: list[str] = []
        if not request.request_id:
            issues.append("Request ID is required.")
        if not request.execution_id:
            issues.append("Execution ID is required.")
        if not request.intent:
            issues.append("Intent is required.")
        if not request.goal:
            issues.append("Goal is required.")
        return (not issues, tuple(issues))

    def validate_response(self, response: ProviderExecutionResponse) -> tuple[bool, tuple[str, ...]]:
        """Validate a provider execution response."""
        issues: list[str] = []
        if response.success and not response.response:
            issues.append("Successful responses must include response content.")
        return (not issues, tuple(issues))

    def validate_record(self, record: ProviderExecutionRecord) -> tuple[bool, tuple[str, ...]]:
        """Validate a provider registry record."""
        issues: list[str] = []
        if not record.provider_id:
            issues.append("Provider ID is required.")
        return (not issues, tuple(issues))
