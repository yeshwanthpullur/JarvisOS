"""Provider execution recovery architecture."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from provider_execution.execution_strategy import FallbackAction


class FailureClassification(StrEnum):
    """Failure classifications used by recovery planning."""

    UNKNOWN = "unknown"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    INVALID_REQUEST = "invalid_request"
    MODEL_UNAVAILABLE = "model_unavailable"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    PERMISSION_DENIED = "permission_denied"


@dataclass(frozen=True, slots=True)
class RecoveryPlan:
    """Provider recovery plan metadata."""

    classification: FailureClassification
    actions: tuple[FallbackAction, ...]
    retry_count: int = 0
    backoff_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class ProviderRecovery:
    """Builds recovery metadata without performing retries."""

    initialized = True

    def __init__(self) -> None:
        self.history: list[RecoveryPlan] = []

    def classify_failure(self, message: str) -> FailureClassification:
        """Classify a failure message."""
        lowered = message.lower()
        if "timeout" in lowered:
            return FailureClassification.TIMEOUT
        if "model" in lowered:
            return FailureClassification.MODEL_UNAVAILABLE
        if "provider" in lowered:
            return FailureClassification.PROVIDER_UNAVAILABLE
        return FailureClassification.UNKNOWN

    def plan(self, message: str, retry_count: int = 0) -> RecoveryPlan:
        """Create and record a recovery plan."""
        classification = self.classify_failure(message)
        actions = (
            FallbackAction.RETRY_SAME_MODEL,
            FallbackAction.RETRY_DIFFERENT_MODEL,
            FallbackAction.RETRY_DIFFERENT_PROVIDER,
            FallbackAction.GRACEFUL_FAILURE,
        )
        plan = RecoveryPlan(
            classification=classification,
            actions=actions,
            retry_count=retry_count,
            backoff_seconds=min(60.0, 2.0 ** retry_count),
        )
        self.history.append(plan)
        return plan

    def statistics(self) -> dict[str, int]:
        """Return recovery statistics."""
        return {"recovery_plans": len(self.history)}
