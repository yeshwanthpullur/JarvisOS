"""Deterministic model route planner; it never executes a model call."""

from __future__ import annotations

from .registry import ModelProviderRegistry
from .types import ModelCapability, ModelProviderStatus, ModelRoute


TASK_CAPABILITIES = {
    "conversation": ModelCapability.CHAT,
    "chat": ModelCapability.CHAT,
    "reasoning": ModelCapability.REASONING,
    "coding": ModelCapability.CODING,
    "vision": ModelCapability.VISION,
    "image_generation": ModelCapability.IMAGE_GENERATION,
    "image": ModelCapability.IMAGE_GENERATION,
    "video": ModelCapability.VIDEO,
    "embeddings": ModelCapability.EMBEDDINGS,
    "speech_to_text": ModelCapability.SPEECH_TO_TEXT,
    "text_to_speech": ModelCapability.TEXT_TO_SPEECH,
    "research": ModelCapability.REASONING,
}


class ModelRouter:
    def __init__(self, registry: ModelProviderRegistry, *, local_only_default: bool = True, allow_cloud_providers: bool = False) -> None:
        self.registry = registry
        self.local_only_default = local_only_default
        self.allow_cloud_providers = allow_cloud_providers

    def route_for_task(self, task_type: str, *, preferred_provider: str | None = None, preferred_model: str | None = None, local_only: bool | None = None) -> ModelRoute:
        task = task_type.strip().lower()
        capability = TASK_CAPABILITIES.get(task, ModelCapability.UNKNOWN)
        local_policy = self.local_only_default if local_only is None else bool(local_only)
        diagnostic_candidates = tuple(
            item for item in self.registry.list_providers()
            if capability in item.capabilities and (not local_policy or item.local)
        )
        all_candidates = tuple(item for item in diagnostic_candidates if item.enabled)
        preferred = self.registry.get_provider(preferred_provider or "")
        selected = None
        if preferred and preferred in all_candidates and preferred.status is ModelProviderStatus.READY:
            selected = preferred
        if selected is None:
            selected = next((item for item in all_candidates if item.status is ModelProviderStatus.READY), None)
        fallbacks = tuple(item.provider_id for item in diagnostic_candidates if item is not selected)[:8]
        if selected is None:
            return ModelRoute(
                task, None, None, capability, ModelProviderStatus.UNAVAILABLE, local_policy,
                "No enabled ready provider supports this task under the local-only policy.", 0.0,
                fallback_routes=fallbacks,
                warnings=("Routing is advisory and performs no model call.",),
            )
        model = preferred_model if preferred_model in selected.available_models else selected.default_model
        return ModelRoute(
            task, selected.provider_id, model, capability, ModelProviderStatus.READY, local_policy,
            f"Selected ready {'local' if selected.local else 'optional'} provider for {capability.value}.",
            0.9, fallback_routes=fallbacks, warnings=("Routing is advisory and performs no model call.",),
        )

    def explain_route(self, task_type: str) -> str:
        route = self.route_for_task(task_type)
        return f"task={route.task_type} capability={route.capability.value} provider={route.selected_provider or 'none'} status={route.status.value} reason={route.reason}"

    def list_routes(self) -> tuple[ModelRoute, ...]:
        return tuple(self.route_for_task(task) for task in TASK_CAPABILITIES)

    def fallback_routes(self, task_type: str) -> tuple[str, ...]:
        return self.route_for_task(task_type).fallback_routes

    def router_status(self) -> dict[str, object]:
        summary = self.registry.registry_summary()
        return {"enabled": True, "status": "ready", "local_only_default": self.local_only_default, "cloud_providers_allowed": self.allow_cloud_providers, **summary}
