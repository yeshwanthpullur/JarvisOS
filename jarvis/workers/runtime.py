"""Integrated pre-old-phone worker and work-intelligence runtime."""

from __future__ import annotations

from pathlib import Path

from .catalog import DynamicModelRegistry, WorkerRoutePlanner, build_provider_registry
from .context import ControlledContextStore
from .models import (
    ContextFragment,
    ContextScope,
    RouteRequest,
    RouteDecision,
    RoutingMode,
    Task,
    WorkerTask,
    WorkRuntimeLimits,
)
from .registry import WorkerRegistry, build_default_worker_registry, opencode_adapter
from .work import GoalWorkManager, WorkStateStore
from .worktrees import WorktreeIsolationManager


class WorkerRuntime:
    """Composes metadata-only workers with existing authority boundaries."""

    def __init__(self, root: Path, limits: WorkRuntimeLimits | None = None) -> None:
        self.root = root.resolve()
        self.limits = limits or WorkRuntimeLimits()
        self.registry: WorkerRegistry = build_default_worker_registry(self.limits.max_workers)
        self.models = DynamicModelRegistry()
        self._ollama_ready = False
        opencode = self.registry.get("opencode")
        self._opencode_detected = bool(opencode and opencode.detected)
        self.providers = build_provider_registry(ollama_detected=False, opencode_detected=self._opencode_detected)
        self.router = WorkerRoutePlanner(self.models, self.limits.max_fallbacks)
        self.context = ControlledContextStore(self.limits.max_context_fragments, self.limits.max_context_chars)
        self.work = GoalWorkManager(self.limits, WorkStateStore(self.root / "data" / "workers" / "state.json"))
        self.worktrees = WorktreeIsolationManager(self.root, self.root / "data" / "agent-workspaces")

    def refresh_workers(self, *, health: bool = False):
        records = self.registry.refresh(health=health)
        opencode = next((item for item in records if item.worker_id == "opencode"), None)
        self._opencode_detected = bool(opencode and opencode.detected)
        self.providers = build_provider_registry(
            ollama_detected=self._ollama_ready,
            opencode_detected=self._opencode_detected,
        )
        return records

    def refresh_models(self):
        adapter = opencode_adapter(self.registry)
        return self.models.refresh_opencode(adapter) if adapter else ()

    def set_ollama_health(self, ready: bool) -> None:
        """Import the authoritative provider health result without probing twice."""
        self._ollama_ready = bool(ready)
        self.providers = build_provider_registry(
            ollama_detected=self._ollama_ready,
            opencode_detected=self._opencode_detected,
        )

    def route(self, request: RouteRequest):
        if not self.limits.enabled:
            return RouteDecision("unavailable", None, None, None, "External worker routing is disabled by configuration.")
        workers = self.refresh_workers()
        ollama = self.providers.get("ollama")
        ollama_ready = bool(ollama and ollama.enabled and self._ollama_ready)
        if not ollama_ready and request.privacy_mode is not RoutingMode.LOCAL_ONLY and not self.limits.allow_cloud_routes:
            return RouteDecision(
                "unavailable",
                None,
                None,
                None,
                "Optional cloud and provider-managed worker routes are disabled by configuration.",
                warnings=("No provider call was attempted.",),
            )
        if not ollama_ready and request.privacy_mode is not RoutingMode.LOCAL_ONLY and not self._opencode_detected:
            return RouteDecision(
                "unavailable",
                None,
                None,
                None,
                "No detected provider-backed worker can satisfy the requested hybrid route.",
                warnings=("Stale dynamic model metadata was not routed.",),
            )
        return self.router.select(request, workers, ollama_ready=ollama_ready)

    def plan_goal(self, objective: str, *, privacy_mode: RoutingMode = RoutingMode.LOCAL_ONLY):
        goal = self.work.create_goal(objective, ("Produce bounded evidence-backed result.", "Preserve approval and review boundaries."))
        decision = self.route(RouteRequest("coding", privacy_mode, requires_repository_write=False, independent_review=True))
        owner = decision.worker_id or "unavailable"
        task = Task(objective, owner, timeout_seconds=self.limits.default_timeout_seconds)
        self.work.add_task(task, goal.goal_id)
        return goal, task, decision

    def status(self) -> dict[str, object]:
        registry = self.registry.summary()
        return {
            "status": "foundation_ready" if self.limits.enabled else "disabled",
            "authority": "plan_route_diagnose_only",
            "registered_workers": registry["registered"],
            "detected_workers": registry["detected"],
            "execution_enabled": registry["execution_enabled"],
            "dynamic_models": len(self.models.list_models()),
            "providers": len(self.providers.list()),
            "max_parallel_tasks": self.limits.max_parallel_tasks,
            "default_routing_mode": self.limits.default_routing_mode,
            "cloud_routes_enabled": self.limits.allow_cloud_routes,
            "worktree_auto_merge": self.limits.worktree_auto_merge,
            "approval_bypass": False,
            "broker_bypass": False,
            "phase7_started": False,
        }


_RUNTIMES: dict[str, WorkerRuntime] = {}


def get_worker_runtime(root: Path | None = None) -> WorkerRuntime:
    resolved = (root or Path.cwd()).resolve()
    key = str(resolved).lower()
    if key not in _RUNTIMES:
        _RUNTIMES[key] = WorkerRuntime(resolved)
    return _RUNTIMES[key]
