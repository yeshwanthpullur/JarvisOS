"""Bounded CLI rendering for Phase 6 environment and local-model metadata."""

from __future__ import annotations

from .models import MODEL_ROLES
from .runtime import Phase6Runtime


def _yes(value: object) -> str:
    return "yes" if value else "no"


def render_phase6_command(runtime: Phase6Runtime, command: str, args: tuple[str, ...]) -> str:
    if command in {"environment status", "tool status"}:
        summary = runtime.environments.summary()
        return "Tool environments: " + " ".join(f"{key}={value}" for key, value in summary.items()) + " installed_is_authorized=no"
    if command in {"environment audit", "tool audit"}:
        audit = runtime.environments.audit(run_pip_check="--pip-check" in args)
        warnings = "; ".join(audit.warnings) or "none"
        return f"Environment audit: python={audit.python_version} environment={audit.environment} isolated={_yes(audit.isolated)} pip={_yes(audit.pip_available)} pip_check={audit.pip_check_status} packages={audit.installed_packages_checked} tools={audit.detected_tools} incompatible={len(audit.incompatible_tools)} warnings={warnings}"[:4000]
    if command == "tool environments":
        records = runtime.environments.refresh()
        return "Tool environments: " + "; ".join(f"{item.tool_id}:{item.install_status}:{item.health_status.value}:enabled={_yes(item.enabled)}:env={item.environment_name}" for item in records)[:6000]
    if command in {"tool inspect", "tool environment-show"}:
        record = runtime.environments.inspect(args[0] if args else "")
        if record is None:
            return "Tool environment not found."
        return f"Tool {record.tool_id}: category={record.category} role={record.primary_or_backup} install={record.install_status} health={record.health_status.value} enabled={_yes(record.enabled)} adapter={record.adapter_type} environment={record.environment_name} python={record.recommended_python} approval={_yes(record.approval_required)} permissions={','.join(record.permission_profile)} fallback={record.fallback} error={record.last_error or 'none'}"[:3000]
    if command in {"provider inspect", "provider test"}:
        provider_id = args[0] if args else "ollama"
        if command == "provider test" and provider_id == "ollama":
            runtime.models.refresh(probe=True)
        provider = runtime.models.provider(provider_id)
        if provider is None:
            return "Provider not found."
        return f"Provider {provider.provider_id}: runtime={provider.runtime} locality={provider.local_or_cloud} configured={_yes(provider.configured)} detected={_yes(provider.detected)} enabled={_yes(provider.enabled)} policy_allowed={_yes(provider.policy_allowed)} approval={_yes(provider.approval_required)} healthy={_yes(provider.healthy)} current_model={provider.current_model or 'none'} models={len(provider.available_models)} error={provider.last_error or 'none'}"[:3000]
    if command in {"model list", "model health"}:
        if command == "model health":
            runtime.models.refresh(probe=True)
        records = runtime.models.models()
        return "Models: " + ("; ".join(f"{item.model_id}:provider={item.provider_id}:healthy={_yes(item.healthy)}:roles={','.join(item.roles)}" for item in records) or "none detected")[:5000]
    if command == "model inspect":
        item = runtime.models.model(args[0] if args else "")
        if item is None:
            return "Model not found; no download was attempted."
        return f"Model {item.model_id}: provider={item.provider_id} runtime={item.runtime} roles={','.join(item.roles)} available={_yes(item.available)} healthy={_yes(item.healthy)} vision={_yes(item.supports_vision)} embeddings={_yes(item.supports_embeddings)} streaming={_yes(item.supports_streaming)} json={_yes(item.supports_json)}"[:3000]
    if command == "model roles":
        return "Model roles: " + "; ".join(f"{role}={getattr(runtime.models.route(role), 'model_id', 'unavailable')}" for role in MODEL_ROLES)
    if command == "model select":
        if len(args) < 2:
            return "Usage: model select <role> <installed_model>. Selection is metadata-only."
        try:
            selected = runtime.models.select(args[0], args[1])
        except ValueError:
            return "Unknown model role."
        return "Model selection updated for this process." if selected else "Model selection unavailable: model is missing, unhealthy, disallowed, or does not support that role."
    if command == "model test":
        runtime.models.refresh(probe=True)
        item = runtime.models.model(args[0] if args else "")
        if item is None:
            return "Model test unavailable: model is not installed. No model was downloaded."
        return f"Model test metadata: model={item.model_id} provider_reachable={_yes(item.healthy)} inference_executed=no. Use normal chat for an authorized local inference test."
    return "Phase 6 command unavailable. No external action was performed."
