"""Policy definitions for adaptive intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AdaptivePolicy:
    executive_approval_required: bool = True
    confidence_threshold: float = 0.75
    risk_threshold: float = 0.35
    rollback_eligibility: bool = True
    expiration_policy: str = "90d"
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self, confidence: float, risk: float) -> bool:
        return confidence >= self.confidence_threshold and risk <= self.risk_threshold
