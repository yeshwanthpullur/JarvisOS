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
    execution_policy: str = "automatic"
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
            execution_policy=str(request.metadata.get("execution_policy", "automatic")),
            metadata=request.metadata,
        )
        candidates = self._candidate_providers(context)
        if not candidates:
            raise LookupError("No provider matches the requested capabilities.")
        attempts: list[dict[str, Any]] = []
        last_response: ProviderResponse | None = None
        for provider in candidates:
            try:
                response = await provider.execute(request)
                if response.error:
                    attempts.append(
                        {
                            "provider": provider.provider_id,
                            "error": response.error,
                            "retryable": response.retryable,
                        }
                    )
                    last_response = response
                    if not response.retryable:
                        break
                    continue
                if attempts:
                    return ProviderResponse(
                        provider_id=response.provider_id,
                        model=response.model,
                        content=response.content,
                        usage=response.usage,
                        metadata={**dict(response.metadata), "fallback": tuple(attempts)},
                        request_id=response.request_id,
                        finish_reason=response.finish_reason,
                        error=response.error,
                        retryable=response.retryable,
                        created_at=response.created_at,
                    )
                return response
            except Exception as exc:  # pragma: no cover - defensive routing
                attempts.append({"provider": provider.provider_id, "error": str(exc), "retryable": True})
                last_response = ProviderResponse(
                    provider_id=provider.provider_id,
                    model=request.model or "",
                    content="",
                    metadata={"fallback": tuple(attempts)},
                    request_id=request.request_id,
                    finish_reason="error",
                    error=str(exc),
                    retryable=True,
                )
                continue
        if last_response is not None:
            return ProviderResponse(
                provider_id=last_response.provider_id,
                model=last_response.model,
                content=last_response.content,
                usage=last_response.usage,
                metadata={**dict(last_response.metadata), "fallback": tuple(attempts)},
                request_id=last_response.request_id,
                finish_reason=last_response.finish_reason,
                error=last_response.error,
                retryable=last_response.retryable,
                created_at=last_response.created_at,
            )
        raise LookupError("No provider could execute the request.")

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
        policy = context.execution_policy.lower()
        if context.local_only or context.offline or policy == "local_only":
            providers = [provider for provider in providers if provider.context.config.local_only]
        elif policy == "cloud_only":
            providers = [provider for provider in providers if not provider.context.config.local_only]
        elif policy == "prefer_local":
            providers.sort(key=lambda provider: not provider.context.config.local_only)
        elif policy == "prefer_cloud":
            providers.sort(key=lambda provider: provider.context.config.local_only)
        return [
            provider
            for provider in providers
            if all(provider.capabilities().supports(capability) for capability in required)
        ]
