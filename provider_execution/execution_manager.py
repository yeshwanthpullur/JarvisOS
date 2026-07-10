"""Provider execution manager for intelligent routing decisions."""

from __future__ import annotations

import logging
import time
from dataclasses import asdict, dataclass
from typing import Any

from providers.provider_types import ProviderCapability
from provider_execution.execution_context import ProviderExecutionContext
from provider_execution.execution_request import ProviderExecutionRequest
from provider_execution.execution_response import ProviderExecutionResponse
from provider_execution.execution_strategy import ExecutionStrategy
from provider_execution.model_selector import ModelMetadata, ModelSelector
from provider_execution.provider_benchmark import ProviderBenchmark
from provider_execution.provider_cache import ProviderCache
from provider_execution.provider_diagnostics import ProviderDiagnostics
from provider_execution.provider_history import ProviderExecutionHistory, ProviderExecutionHistoryRecord
from provider_execution.provider_recovery import ProviderRecovery
from provider_execution.provider_registry import ProviderExecutionRecord, ProviderExecutionRegistry
from provider_execution.provider_selector import ProviderSelector
from provider_execution.provider_validator import ProviderExecutionValidator


@dataclass(frozen=True, slots=True)
class ProviderExecutionStatistics:
    """Startup and runtime statistics for the provider execution framework."""

    registered_providers: int
    enabled_providers: int
    healthy_providers: int
    registered_models: int
    executions: int
    status: str = "ready"


class ExecutionManager:
    """Coordinates intelligent provider and model selection.

    The manager prepares execution metadata and routes only through the existing
    ProviderRouter. It intentionally does not call provider APIs.
    """

    def __init__(
        self,
        context: ProviderExecutionContext | None = None,
        registry: ProviderExecutionRegistry | None = None,
        selector: ProviderSelector | None = None,
        model_selector: ModelSelector | None = None,
        validator: ProviderExecutionValidator | None = None,
        history: ProviderExecutionHistory | None = None,
        cache: ProviderCache | None = None,
        recovery: ProviderRecovery | None = None,
        diagnostics: ProviderDiagnostics | None = None,
        benchmark: ProviderBenchmark | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.context = context or ProviderExecutionContext()
        self.registry = registry or ProviderExecutionRegistry(logger=logger)
        self.selector = selector or ProviderSelector(logger=logger)
        self.model_selector = model_selector or ModelSelector(logger=logger)
        self.validator = validator or ProviderExecutionValidator()
        self.history = history or ProviderExecutionHistory()
        self.cache = cache or ProviderCache()
        self.recovery = recovery or ProviderRecovery()
        self.diagnostics = diagnostics or ProviderDiagnostics()
        self.benchmark = benchmark or ProviderBenchmark()
        self.logger = logger or self.context.logger
        self.initialized = False

    def initialize(self) -> ProviderExecutionStatistics:
        """Initialize provider execution metadata from existing provider systems."""
        self.registry.load_from_provider_manager(self.context.provider_manager)
        self.initialized = True
        self.logger.info("provider_execution_initialized registered=%s", self.statistics().registered_providers)
        return self.statistics()

    def build_execution_request(
        self,
        intent: str,
        goal: str,
        **metadata: Any,
    ) -> ProviderExecutionRequest:
        """Build a normalized provider execution request."""
        request = ProviderExecutionRequest(
            intent=intent,
            goal=goal,
            conversation_id=metadata.get("conversation_id"),
            priority=int(metadata.get("priority", 5)),
            complexity=float(metadata.get("complexity", self.estimate_complexity(goal))),
            estimated_tokens=int(metadata.get("estimated_tokens", self.estimate_tokens(goal))),
            estimated_cost=float(metadata.get("estimated_cost", 0.0)),
            department=metadata.get("department"),
            agent=metadata.get("agent"),
            provider=metadata.get("provider"),
            model=metadata.get("model"),
            capabilities=tuple(metadata.get("capabilities", ()) or ()),
            strategy=metadata.get("strategy", ExecutionStrategy.SINGLE_PROVIDER),
            context=dict(metadata.get("context", {}) or {}),
            metadata=dict(metadata.get("metadata", {}) or {}),
        )
        return self.analyze_request(request)

    def analyze_request(self, request: ProviderExecutionRequest) -> ProviderExecutionRequest:
        """Analyze request metadata and infer missing strategy/capabilities."""
        capabilities = request.capabilities or self._capabilities_for_intent(request.intent)
        strategy = self.determine_strategy(request)
        return ProviderExecutionRequest(
            intent=request.intent,
            goal=request.goal,
            request_id=request.request_id,
            conversation_id=request.conversation_id,
            execution_id=request.execution_id,
            priority=request.priority,
            complexity=request.complexity or self.estimate_complexity(request.goal),
            estimated_tokens=request.estimated_tokens or self.estimate_tokens(request.goal),
            estimated_cost=request.estimated_cost or self.estimate_cost(request),
            department=request.department,
            agent=request.agent,
            provider=request.provider,
            model=request.model,
            capabilities=capabilities,
            strategy=strategy,
            context=request.context,
            metadata=request.metadata,
        )

    def estimate_complexity(self, goal: str) -> float:
        """Estimate request complexity with a deterministic heuristic."""
        words = len(goal.split())
        return min(1.0, words / 200)

    def estimate_cost(self, request: ProviderExecutionRequest) -> float:
        """Estimate cost metadata without provider API calls."""
        return round((request.estimated_tokens or self.estimate_tokens(request.goal)) * 0.0, 6)

    def estimate_latency(self, provider: ProviderExecutionRecord | None = None) -> float:
        """Estimate latency from provider health metadata."""
        return 0.0 if provider is None else provider.health.latency_ms

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count using the existing provider-neutral heuristic."""
        return max(1, len(text) // 4) if text else 0

    def determine_strategy(self, request: ProviderExecutionRequest) -> ExecutionStrategy:
        """Determine an execution strategy from request metadata."""
        if request.strategy is not ExecutionStrategy.SINGLE_PROVIDER:
            return request.strategy
        if request.metadata.get("local_only"):
            return ExecutionStrategy.LOCAL_FIRST
        if request.metadata.get("multi_provider"):
            return ExecutionStrategy.MULTI_PROVIDER
        if request.metadata.get("fallback"):
            return ExecutionStrategy.FALLBACK
        return ExecutionStrategy.SINGLE_PROVIDER

    def select_provider(self, request: ProviderExecutionRequest) -> ProviderExecutionRecord | None:
        """Select a provider record for a request."""
        return self.selector.select(request, self.registry)

    def select_model(
        self,
        provider: ProviderExecutionRecord | None,
        request: ProviderExecutionRequest,
    ) -> ModelMetadata | None:
        """Select a model for the provider."""
        if provider is None:
            return None
        return self.model_selector.select_model(provider, request)

    def execute(self, request: ProviderExecutionRequest) -> ProviderExecutionResponse:
        """Prepare provider execution and return an architectural response.

        Real provider calls are intentionally not implemented. The method still
        validates, selects, records metrics, and returns clear diagnostics.
        """
        start = time.perf_counter()
        is_valid, issues = self.validator.validate_request(request)
        if not is_valid:
            return self._failure_response(request, "Invalid provider execution request.", issues, start)

        provider = self.select_provider(request)
        model = self.select_model(provider, request)
        if provider is None:
            return self._failure_response(request, "No provider matched the execution request.", (), start)

        provider.metrics.record_request(request.estimated_tokens, request.estimated_cost)
        latency = self.estimate_latency(provider)
        elapsed_ms = (time.perf_counter() - start) * 1000
        model_id = model.model_id if model is not None else request.model
        response = ProviderExecutionResponse(
            response="Provider execution prepared. Real AI provider calls are not implemented yet.",
            provider=provider.provider_id,
            model=model_id,
            execution_time_ms=elapsed_ms,
            latency_ms=latency,
            estimated_cost=request.estimated_cost,
            token_metadata={"estimated_tokens": request.estimated_tokens},
            warnings=("provider_api_execution_not_implemented",),
            diagnostics={
                "strategy": request.strategy.value,
                "capabilities": [capability.value for capability in request.capabilities],
            },
            statistics=asdict(self.statistics()),
            success=True,
        )
        provider.metrics.record_response(latency)
        self._record_history(request, response)
        return response

    def execute_through_provider_router(self, request: ProviderExecutionRequest) -> ProviderExecutionResponse:
        """Compatibility method naming the only allowed execution gateway."""
        return self.execute(request)

    def handle_failures(self, request: ProviderExecutionRequest, message: str) -> ProviderExecutionResponse:
        """Create recovery metadata for a provider failure."""
        plan = self.recovery.plan(message)
        return self._failure_response(
            request,
            message,
            tuple(action.value for action in plan.actions),
            time.perf_counter(),
            recovery=plan.classification.value,
        )

    def handle_recovery(self, message: str) -> dict[str, object]:
        """Return recovery plan metadata."""
        plan = self.recovery.plan(message)
        return {
            "classification": plan.classification.value,
            "actions": [action.value for action in plan.actions],
            "retry_count": plan.retry_count,
            "backoff_seconds": plan.backoff_seconds,
        }

    def validate_response(self, response: ProviderExecutionResponse) -> tuple[bool, tuple[str, ...]]:
        """Validate a provider execution response."""
        return self.validator.validate_response(response)

    def statistics(self) -> ProviderExecutionStatistics:
        """Return provider execution statistics."""
        registry_stats = self.registry.statistics()
        model_stats = self.model_selector.statistics()
        history_stats = self.history.statistics()
        return ProviderExecutionStatistics(
            registered_providers=registry_stats["registered_providers"],
            enabled_providers=registry_stats["enabled_providers"],
            healthy_providers=registry_stats["healthy_providers"],
            registered_models=model_stats["registered_models"],
            executions=history_stats["executions"],
            status="ready" if self.initialized else "created",
        )

    def _capabilities_for_intent(self, intent: str) -> tuple[ProviderCapability, ...]:
        intent_value = intent.lower()
        if "code" in intent_value or "coding" in intent_value:
            return (ProviderCapability.CODING,)
        if "reason" in intent_value or "planning" in intent_value:
            return (ProviderCapability.REASONING,)
        if "vision" in intent_value or "image" in intent_value:
            return (ProviderCapability.VISION,)
        return (ProviderCapability.CHAT,)

    def _failure_response(
        self,
        request: ProviderExecutionRequest,
        message: str,
        warnings: tuple[str, ...],
        start: float,
        recovery: str | None = None,
    ) -> ProviderExecutionResponse:
        elapsed_ms = (time.perf_counter() - start) * 1000
        response = ProviderExecutionResponse(
            response=message,
            execution_time_ms=elapsed_ms,
            warnings=warnings,
            diagnostics={"recovery": recovery} if recovery else {},
            success=False,
        )
        self._record_history(request, response, failure=message, recovery=recovery)
        return response

    def _record_history(
        self,
        request: ProviderExecutionRequest,
        response: ProviderExecutionResponse,
        failure: str | None = None,
        recovery: str | None = None,
    ) -> None:
        self.history.append(
            ProviderExecutionHistoryRecord(
                execution_id=request.execution_id,
                provider=response.provider,
                model=response.model,
                department=request.department,
                agent=request.agent,
                execution_strategy=request.strategy,
                latency_ms=response.latency_ms,
                estimated_cost=response.estimated_cost,
                estimated_tokens=request.estimated_tokens,
                success=response.success,
                failure=failure,
                recovery=recovery,
                metadata=response.diagnostics,
            )
        )
