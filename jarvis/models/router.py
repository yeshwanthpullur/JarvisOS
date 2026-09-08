"""Deterministic model route planner; it never executes a model call."""

from __future__ import annotations

from .registry import ModelProviderRegistry
from .privacy import PrivacyMode, PrivacyPolicy
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
    "research_planning": ModelCapability.REASONING,
    "document": ModelCapability.DOCUMENT_QUESTION_ANSWERING,
    "document_question_answering": ModelCapability.DOCUMENT_QUESTION_ANSWERING,
    "browser": ModelCapability.BROWSER_SUMMARIZATION,
    "browser_summarization": ModelCapability.BROWSER_SUMMARIZATION,
    "scheduler": ModelCapability.SCHEDULER_PLANNING,
    "scheduler_planning": ModelCapability.SCHEDULER_PLANNING,
    "communication": ModelCapability.COMMUNICATION_DRAFTING,
    "communication_drafting": ModelCapability.COMMUNICATION_DRAFTING,
    "adapter": ModelCapability.ADAPTER_PLANNING,
    "adapter_planning": ModelCapability.ADAPTER_PLANNING,
}


class ModelRouter:
    def __init__(self, registry: ModelProviderRegistry, *, local_only_default: bool = True, allow_cloud_providers: bool = False, privacy_mode: PrivacyMode | str | None = None) -> None:
        self.registry = registry
        self.local_only_default = local_only_default
        self.allow_cloud_providers = allow_cloud_providers
        self.privacy_policy = PrivacyPolicy.from_value(privacy_mode or (PrivacyMode.LOCAL_ONLY if local_only_default else PrivacyMode.NORMAL_HYBRID), allow_cloud_providers=allow_cloud_providers)

    def route_for_task(self, task_type: str, *, preferred_provider: str | None = None, preferred_model: str | None = None, local_only: bool | None = None, privacy_mode: PrivacyMode | str | None = None) -> ModelRoute:
        task = task_type.strip().lower()
        capability = TASK_CAPABILITIES.get(task, ModelCapability.UNKNOWN)
        local_policy = self.local_only_default if local_only is None else bool(local_only)
        policy = PrivacyPolicy.from_value(privacy_mode or self.privacy_policy.mode, allow_cloud_providers=self.allow_cloud_providers)
        if local_only is True:
            policy = PrivacyPolicy.from_value(PrivacyMode.LOCAL_ONLY, allow_cloud_providers=False)
        def matches_privacy_scope(item):
            if item.privacy_mode.value == "cloud_only_blocked":
                return False
            if policy.mode is PrivacyMode.LOCAL_ONLY and not item.local:
                return False
            if not item.local and not policy.allow_cloud_providers:
                return False
            if policy.mode is PrivacyMode.PRIVATE_HYBRID and not item.local and item.privacy_mode.value != "optional_cloud":
                return False
            return True

        # Keep unavailable providers in diagnostics/fallbacks, but never select
        # them. This preserves truthful explanations without weakening routing.
        diagnostic_candidates = tuple(
            item for item in self.registry.list_providers()
            if capability in item.capabilities and matches_privacy_scope(item)
        )
        all_candidates = tuple(item for item in diagnostic_candidates if item.enabled and policy.evaluate(item).allowed)
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
                f"No enabled ready provider supports this task under the {policy.mode.value} privacy policy.", 0.0,
                fallback_routes=fallbacks,
                warnings=("Routing is advisory and performs no model call.",),
            )
        model = preferred_model if preferred_model in selected.available_models else selected.default_model
        return ModelRoute(
            task, selected.provider_id, model, capability, ModelProviderStatus.READY, local_policy,
            f"Selected ready {'local' if selected.local else 'optional'} provider for {capability.value} under {policy.mode.value}.",
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
        return {"enabled": True, "status": "ready", "privacy_mode": self.privacy_policy.mode.value, "local_only_default": self.local_only_default, "cloud_providers_allowed": self.allow_cloud_providers, **summary}
