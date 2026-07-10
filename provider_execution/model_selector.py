"""Model selection architecture for provider execution."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from providers.provider_types import ProviderCapability
from provider_execution.execution_request import ProviderExecutionRequest
from provider_execution.provider_registry import ProviderExecutionRecord


@dataclass(frozen=True, slots=True)
class ModelMetadata:
    """Execution metadata for one model."""

    model_id: str
    provider_id: str
    capabilities: tuple[ProviderCapability, ...] = ()
    context_window: int = 0
    reasoning_support: bool = False
    tool_calling: bool = False
    vision_support: bool = False
    embedding_support: bool = False
    latency_ms: float = 0.0
    estimated_cost: float = 0.0
    reliability: float = 1.0
    historical_performance: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


class ModelSelector:
    """Ranks and selects models without invoking provider APIs."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._models: dict[tuple[str, str], ModelMetadata] = {}
        self.initialized = True
        self._logger = logger or logging.getLogger(__name__)

    def discover_models(self, provider: ProviderExecutionRecord) -> tuple[ModelMetadata, ...]:
        """Discover known models from provider capability metadata."""
        discovered = []
        for model in provider.capabilities.models:
            metadata = ModelMetadata(
                model_id=model.model_id,
                provider_id=provider.provider_id,
                capabilities=tuple(model.capabilities),
                context_window=model.context_window,
            )
            self.register_model(metadata)
            discovered.append(metadata)
        return tuple(discovered)

    def register_model(self, model: ModelMetadata) -> None:
        """Register or replace model metadata."""
        self._models[(model.provider_id, model.model_id)] = model

    def validate_model(self, model: ModelMetadata) -> bool:
        """Validate model metadata."""
        return bool(model.provider_id and model.model_id)

    def rank_models(
        self,
        provider: ProviderExecutionRecord,
        request: ProviderExecutionRequest,
    ) -> tuple[ModelMetadata, ...]:
        """Rank models for a provider and request."""
        models = list(self.discover_models(provider))
        if request.model:
            models.sort(key=lambda model: model.model_id != request.model)
        models = [
            model for model in models
            if all(capability in model.capabilities for capability in request.capabilities)
        ] or models
        models.sort(key=self._score, reverse=True)
        return tuple(models)

    def select_model(
        self,
        provider: ProviderExecutionRecord,
        request: ProviderExecutionRequest,
    ) -> ModelMetadata | None:
        """Select the best model for a provider request."""
        ranked = self.rank_models(provider, request)
        if ranked:
            return ranked[0]
        if request.model:
            return ModelMetadata(model_id=request.model, provider_id=provider.provider_id)
        return None

    def fallback_model(self, provider: ProviderExecutionRecord, failed_model: str | None = None) -> ModelMetadata | None:
        """Return a fallback model different from the failed model when possible."""
        for model in self.discover_models(provider):
            if model.model_id != failed_model:
                return model
        return None

    def recovery_model(self, provider: ProviderExecutionRecord) -> ModelMetadata | None:
        """Return the model currently preferred for recovery attempts."""
        return self.fallback_model(provider)

    def collect_metrics(self, model: ModelMetadata) -> dict[str, object]:
        """Return model metric metadata."""
        return {"model_id": model.model_id, "latency_ms": model.latency_ms, "reliability": model.reliability}

    def benchmark_models(self, provider: ProviderExecutionRecord) -> tuple[ModelMetadata, ...]:
        """Return models ordered for future benchmarking."""
        return tuple(sorted(self.discover_models(provider), key=self._score, reverse=True))

    def statistics(self) -> dict[str, int]:
        """Return model selector statistics."""
        return {"registered_models": len(self._models)}

    def _score(self, model: ModelMetadata) -> float:
        cost_penalty = min(model.estimated_cost, 1.0)
        latency_penalty = min(model.latency_ms / 10000, 1.0)
        return model.reliability + model.historical_performance - cost_penalty - latency_penalty
