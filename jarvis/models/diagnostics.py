"""Bounded model registry and router CLI rendering."""

from __future__ import annotations

from .hardware import safe_hardware_summary
from .registry import ModelProviderRegistry
from .router import ModelRouter


def render_model_command(registry: ModelProviderRegistry, router: ModelRouter, command: str, arguments: tuple[str, ...]) -> str:
    if command == "model status":
        data = router.router_status()
        return "Model Router: " + " ".join(f"{key}={str(value).lower() if isinstance(value, bool) else value}" for key, value in data.items())
    if command == "model providers":
        return "Model providers: " + ", ".join(f"{item.provider_id}:{item.status.value}" for item in registry.list_providers()[:20])
    if command == "model capabilities":
        return "Model capabilities: " + ", ".join(f"{provider}.{capability}:{status}" for provider, capability, status in registry.list_capabilities()[:40])
    if command == "model hardware":
        return "Model hardware: " + " ".join(f"{key}={value}" for key, value in safe_hardware_summary().items())
    if command == "model policy":
        return "Model policy: local_only_default=on cloud_providers=disabled automatic_downloads=off public_local_endpoints=blocked."
    task = " ".join(arguments).strip()
    if not task:
        return f"Usage: {command} <task>"
    if command == "model explain":
        return "Model explanation: " + router.explain_route(task)
    route = router.route_for_task(task)
    return f"Model route: task={route.task_type} capability={route.capability.value} provider={route.selected_provider or 'none'} model={route.selected_model or 'none'} status={route.status.value} local_only={'yes' if route.local_only else 'no'}."

