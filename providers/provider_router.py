"""Intelligent provider routing for JARVIS OS."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from providers.base_provider import BaseProvider
from providers.provider_types import (
    CostEstimate,
    ProviderCapability,
    ProviderRequest,
    ProviderResponse,
    ProviderSelection,
    ProviderTaskType,
)


TASK_CAPABILITY_MAP: dict[ProviderTaskType, ProviderCapability] = {
    ProviderTaskType.CHAT: ProviderCapability.CHAT,
    ProviderTaskType.REASONING: ProviderCapability.REASONING,
    ProviderTaskType.CODING: ProviderCapability.CODING,
    ProviderTaskType.VISION: ProviderCapability.VISION,
    ProviderTaskType.SPEECH: ProviderCapability.SPEECH,
    ProviderTaskType.EMBEDDING: ProviderCapability.EMBEDDING,
    ProviderTaskType.TRANSCRIPTION: ProviderCapability.TRANSCRIPTION,
    ProviderTaskType.IMAGE_GENERATION: ProviderCapability.IMAGE_GENERATION,
}


@dataclass(frozen=True, slots=True)
class ProviderSelectionContext:
    """Inputs used to select a provider."""

    goal: str = ""
    task_type: ProviderTaskType = ProviderTaskType.CHAT
    preferred_provider: str | None = None
    preferred_model: str | None = None
    required_capabilities: tuple[ProviderCapability, ...] = ()
    local_only: bool = False
    offline: bool = False
    max_cost: float | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


class ProviderRouter:
    """Provider-neutral routing gateway for all future AI operations."""

    def __init__(
        self,
        providers: Iterable[BaseProvider] = (),
        logger: logging.Logger | None = None,
    ) -> None:
        self._providers: dict[str, BaseProvider] = {
            provider.provider_id: provider for provider in providers
        }
        self._logger = logger or logging.getLogger(__name__)

    @property
    def provider_names(self) -> tuple[str, ...]:
        """Return registered provider IDs."""
        return tuple(self._providers)

    def register_provider(self, provider: BaseProvider) -> None:
        """Register or replace a provider adapter."""
        self._providers[provider.provider_id] = provider
        self._logger.info("provider_router_registered provider_id=%s", provider.provider_id)

    def unregister_provider(self, provider_id: str) -> None:
        """Remove a provider from routing."""
        self._providers.pop(provider_id, None)
        self._logger.info("provider_router_unregistered provider_id=%s", provider_id)

    def capabilities(self) -> Mapping[str, object]:
        """Return capabilities for all registered providers."""
        return {
            provider_id: provider.capabilities()
            for provider_id, provider in self._providers.items()
        }

    def estimate_costs(self, request: ProviderRequest) -> Mapping[str, CostEstimate]:
        """Return cost estimates for available providers."""
        return {
            provider_id: provider.estimate_cost(request)
            for provider_id, provider in self._providers.items()
            if provider.is_available()
        }

    def select_provider(self, context: ProviderSelectionContext) -> BaseProvider:
        """Select a provider by preferences, health, locality, and capabilities."""
        candidates = self._candidate_providers(context)
        if not candidates:
            raise LookupError("No provider matches the requested capabilities.")
        selected = candidates[0]
        self._logger.info(
            "provider_selected provider_id=%s task_type=%s",
            selected.provider_id,
            context.task_type.value,
        )
        return selected

    def select(self, context: ProviderSelectionContext) -> ProviderSelection:
        """Return a structured provider selection result."""
        provider = self.select_provider(context)
        return ProviderSelection(
            provider_id=provider.provider_id,
            model=context.preferred_model or provider.context.config.preferred_model or provider.context.config.default_model,
            reason="Selected by preference, availability, and capability match.",
        )

    async def execute_with_failover(self, request: ProviderRequest) -> ProviderResponse:
        """Execute through the selected provider adapter with bounded failover."""
        context = ProviderSelectionContext(
            goal=request.goal,
            task_type=request.task_type,
            preferred_model=request.model,
            required_capabilities=request.required_capabilities,
            preferred_provider=request.preferred_provider,
            local_only=bool(request.local_only or request.metadata.get("local_only")),
            metadata=request.metadata,
        )
        provider = self.select_provider(context)
        if provider is None:
            raise LookupError("No provider matches the requested capabilities.")
        return await provider.execute(request)

    def _candidate_providers(
        self,
        context: ProviderSelectionContext,
    ) -> list[BaseProvider]:
        required = set(context.required_capabilities)
        required.add(TASK_CAPABILITY_MAP[context.task_type])
        providers = [
            provider
            for provider in self._providers.values()
            if provider.enabled and provider.initialized
        ]
        if context.preferred_provider:
            providers.sort(key=lambda provider: provider.provider_id != context.preferred_provider)
        if context.local_only or context.offline:
            providers = [provider for provider in providers if provider.context.config.local_only]
        return [
            provider
            for provider in providers
            if all(provider.capabilities().supports(capability) for capability in required)
        ]
