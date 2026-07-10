"""Provider execution request envelope."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from providers.provider_types import ProviderCapability
from provider_execution.execution_strategy import ExecutionStrategy


@dataclass(frozen=True, slots=True)
class ProviderExecutionRequest:
    """Normalized request used before selecting a provider and model."""

    intent: str
    goal: str
    request_id: str = field(default_factory=lambda: str(uuid4()))
    conversation_id: str | None = None
    execution_id: str = field(default_factory=lambda: str(uuid4()))
    priority: int = 5
    complexity: float = 0.0
    estimated_tokens: int = 0
    estimated_cost: float = 0.0
    department: str | None = None
    agent: str | None = None
    provider: str | None = None
    model: str | None = None
    capabilities: tuple[ProviderCapability, ...] = ()
    strategy: ExecutionStrategy = ExecutionStrategy.SINGLE_PROVIDER
    context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
