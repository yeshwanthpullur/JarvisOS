"""Provider-neutral dynamic model catalog and conservative route planner."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

from .adapters import OpenCodeAdapter
from .models import (
    DynamicModelRecord,
    ModelAlias,
    ProviderRecord,
    RouteDecision,
    RouteRequest,
    RoutingMode,
    WorkerRecord,
    WorkerStatus,
    now,
)


class DynamicModelRegistry:
    def __init__(self, max_models: int = 128) -> None:
        self.max_models = max(1, min(max_models, 512))
        self._models: dict[str, DynamicModelRecord] = {}
        self._aliases: dict[str, ModelAlias] = {
            "ox-alpha": ModelAlias(
                "ox-alpha",
                None,
                "unresolved",
                "Exact OpenCode model identifier was not discovered; no successor was guessed.",
                source="awaiting_opencode_discovery",
            ),
        }

    def refresh_opencode(self, adapter: OpenCodeAdapter) -> tuple[DynamicModelRecord, ...]:
        discovered = set(adapter.discover_models())
        for model_id, current in tuple(self._models.items()):
            if current.provider_id == "opencode" and model_id not in discovered:
                self._models[model_id] = replace(current, status="unavailable", reason="Not returned by the latest bounded discovery refresh.")
        for model_id in sorted(discovered)[: self.max_models]:
            lower = model_id.lower()
            free = lower.endswith("-free") or lower.endswith("/free")
            temporary = any(word in lower for word in ("preview", "experimental", "temporary"))
            self._models[model_id] = DynamicModelRecord(
                model_id,
                "opencode",
                aliases=(),
                capabilities=("chat", "coding", "reasoning"),
                cost_class="free" if free else "unknown",
                exact_price_known=False,
                free=True if free else None,
                temporary=temporary,
                source="opencode models",
                reason="Discovered from the installed OpenCode catalog; availability may change.",
                display_name=model_id.rsplit("/", 1)[-1],
                context_metadata="not_reported_by_catalog",
                speed_class="unknown",
                privacy_class="provider_dependent",
                locality="cloud_or_provider_managed",
                last_seen=now(),
                last_checked=now(),
            )
        exact = next((model_id for model_id in discovered if model_id.lower() == "ox-alpha" or model_id.lower().endswith("/ox-alpha")), None)
        self._aliases["ox-alpha"] = ModelAlias(
            "ox-alpha",
            exact,
            "resolved" if exact else "unresolved",
            "Exact identifier discovered." if exact else "Exact OpenCode model identifier was not discovered; no successor was guessed.",
            possible_successor=None,
            last_checked=now(),
            source="opencode models",
        )
        return self.list_models(provider_id="opencode")

    def register(self, model: DynamicModelRecord) -> None:
        if len(self._models) >= self.max_models and model.model_id not in self._models:
            raise ValueError("dynamic_model_limit_exceeded")
        self._models[model.model_id] = model

    def list_models(self, provider_id: str = "") -> tuple[DynamicModelRecord, ...]:
        return tuple(
            self._models[key]
            for key in sorted(self._models)
            if not provider_id or self._models[key].provider_id == provider_id
        )

    def get(self, model_id_or_alias: str) -> DynamicModelRecord | None:
        alias = self._aliases.get(model_id_or_alias)
        key = alias.target_model_id if alias and alias.target_model_id else model_id_or_alias
        return self._models.get(key)

    def alias(self, name: str) -> ModelAlias | None:
        return self._aliases.get(name)

    def aliases(self) -> tuple[ModelAlias, ...]:
        return tuple(self._aliases[key] for key in sorted(self._aliases))

    def expire_temporary(self, current: datetime | None = None) -> tuple[str, ...]:
        current = current or datetime.now(UTC)
        expired = []
        for model_id, model in tuple(self._models.items()):
            if not model.temporary or not model.expires_at:
                continue
            try:
                deadline = datetime.fromisoformat(model.expires_at)
            except ValueError:
                self._models[model_id] = replace(model, status="unavailable", reason="Temporary model expiration metadata was malformed.")
                expired.append(model_id)
                continue
            if deadline <= current:
                self._models[model_id] = replace(model, status="unavailable", reason="Temporary model availability expired.")
                expired.append(model_id)
        return tuple(expired)


class WorkerProviderRegistry:
    def __init__(self, providers: tuple[ProviderRecord, ...]) -> None:
        self._providers: dict[str, ProviderRecord] = {}
        for provider in providers:
            if provider.provider_id in self._providers:
                raise ValueError(f"duplicate_worker_provider:{provider.provider_id}")
            self._providers[provider.provider_id] = provider

    def list(self) -> tuple[ProviderRecord, ...]:
        return tuple(self._providers[key] for key in sorted(self._providers))

    def get(self, provider_id: str) -> ProviderRecord | None:
        return self._providers.get(provider_id)


def build_provider_registry(*, ollama_detected: bool = False, opencode_detected: bool = False) -> WorkerProviderRegistry:
    return WorkerProviderRegistry((
        ProviderRecord("ollama", "local_model_runtime", "local", "detected" if ollama_detected else "unavailable", enabled=ollama_detected, cost_class="local", privacy_class="local_only", capabilities=("chat", "coding", "reasoning"), reason="Existing local Ollama runtime; preferred when healthy.", base_reference="loopback_local", configured=ollama_detected, health="detected" if ollama_detected else "unavailable"),
        ProviderRecord("opencode", "agent_model_catalog", "hybrid", "discovery_only" if opencode_detected else "unavailable", enabled=opencode_detected, cost_class="mixed", privacy_class="model_dependent", capabilities=("chat", "coding", "reasoning"), reason="Models are refreshed dynamically through bounded OpenCode metadata discovery." if opencode_detected else "OpenCode executable was not detected; no installation was attempted.", base_reference="installed_cli", configured=opencode_detected, health="metadata_only" if opencode_detected else "unavailable"),
        ProviderRecord("openrouter", "cloud_gateway", "cloud", "not_configured", "OPENROUTER_API_KEY_ENV", False, "unknown", "external", ("chat", "coding", "reasoning"), "Credential reference only; no secret was read."),
        ProviderRecord("tokenrouter", "cloud_gateway", "cloud", "not_configured", "TOKENROUTER_API_KEY_ENV", False, "unknown", "external", ("chat", "coding"), "Future provider reference; disabled by default."),
        ProviderRecord("zenmux", "cloud_gateway", "cloud", "not_configured", "ZENMUX_API_KEY_ENV", False, "unknown", "external", ("chat", "coding", "reasoning"), "Credential reference only; disabled by default."),
        ProviderRecord("openai", "cloud_provider", "cloud", "not_configured", "OPENAI_API_KEY_ENV", False, "unknown", "external", ("chat", "coding", "reasoning"), "Future provider reference; disabled by default."),
        ProviderRecord("anthropic", "cloud_provider", "cloud", "not_configured", "ANTHROPIC_API_KEY_ENV", False, "unknown", "external", ("chat", "coding", "reasoning"), "Future provider reference; disabled by default."),
        ProviderRecord("google", "cloud_provider", "cloud", "not_configured", "GOOGLE_API_KEY_ENV", False, "unknown", "external", ("chat", "coding", "reasoning"), "Future provider reference; disabled by default."),
        ProviderRecord("deepseek", "cloud_provider", "cloud", "not_configured", "DEEPSEEK_API_KEY_ENV", False, "unknown", "external", ("chat", "coding", "reasoning"), "Future provider reference; disabled by default."),
        ProviderRecord("qwen", "cloud_or_local_provider", "hybrid", "not_configured", "QWEN_API_KEY_ENV", False, "unknown", "model_dependent", ("chat", "coding", "reasoning"), "No local or cloud route was configured automatically."),
    ))


class WorkerRoutePlanner:
    def __init__(self, models: DynamicModelRegistry, max_fallbacks: int = 2) -> None:
        self.models = models
        self.max_fallbacks = max(0, min(max_fallbacks, 4))

    def select(self, request: RouteRequest, workers: tuple[WorkerRecord, ...], *, ollama_ready: bool) -> RouteDecision:
        available = tuple(item for item in workers if item.status in {WorkerStatus.DEGRADED, WorkerStatus.READY})
        preferred = next((item for item in available if item.worker_id == request.preferred_worker), None)
        task = request.task_type.lower()
        desired = (
            "aider" if any(value in task for value in ("small edit", "targeted edit"))
            else "hermes" if any(value in task for value in ("general delegated", "general work"))
            else "opencode" if "opencode" in task
            else "codex"
        )
        if any(value in task for value in ("architecture", "review")):
            candidate = preferred or next((item for item in available if item.capabilities.independent_review), None)
        else:
            candidate = preferred or next((item for item in available if item.worker_id == desired), None)
        candidate = candidate or next((item for item in available if item.worker_id == "codex"), None) or (available[0] if available else None)
        fallbacks = tuple(item.worker_id for item in available if item is not candidate)[: self.max_fallbacks]
        approval = request.requires_repository_write or request.risk_level.lower() in {"high", "critical"}
        reviewer = None
        if request.independent_review and candidate:
            reviewer = next((item.worker_id for item in available if item.worker_id != candidate.worker_id and item.capabilities.independent_review), None)
        if candidate is None:
            return RouteDecision("unavailable", None, None, None, "No detected worker can plan this task.", warnings=("No installation was attempted.",))
        if not request.online and not ollama_ready:
            return RouteDecision("unavailable", candidate.worker_id, None, None, "Offline routing requires a healthy local model.", fallbacks, reviewer, approval)
        if request.workspace_requirement not in candidate.workspace_modes:
            return RouteDecision("unavailable", candidate.worker_id, None, None, "Selected worker does not support the required bounded workspace mode.", fallbacks, reviewer, approval)
        if ollama_ready:
            provider, model = "ollama", None
            reason = "Selected the existing healthy local provider before optional external routes."
        elif request.privacy_mode in {RoutingMode.LOCAL_ONLY, RoutingMode.PRIVATE_HYBRID}:
            return RouteDecision("unavailable", candidate.worker_id, None, None, "A local model route is required but no healthy local model was verified.", fallbacks, reviewer, approval)
        else:
            candidates = tuple(item for item in self.models.list_models("opencode") if item.status == "available" and (item.free is True or request.max_cost_class != "free_only"))
            selected = next((item for item in candidates if item.model_id == request.preferred_model), None) or (candidates[0] if candidates else None)
            if selected is None:
                return RouteDecision("unavailable", candidate.worker_id, None, None, "No dynamically discovered model satisfies the route policy.", fallbacks, reviewer, approval)
            provider, model = "opencode", selected.model_id
            reason = "Selected a dynamically discovered OpenCode model; exact price is not claimed."
        return RouteDecision("planned", candidate.worker_id, provider, model, reason, fallbacks, reviewer, approval, "plan_only", ("Routing grants no execution authority.",))
