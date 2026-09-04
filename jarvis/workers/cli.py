"""Bounded CLI rendering for worker and work-intelligence diagnostics."""

from __future__ import annotations

from .models import RouteRequest, RoutingMode, WorkerTask
from .runtime import WorkerRuntime


def _yes(value: object) -> str:
    return "yes" if bool(value) else "no"


def render_worker_command(runtime: WorkerRuntime, command: str, args: tuple[str, ...]) -> str:
    if command in {"worker status", "work status"}:
        values = runtime.status() if command == "worker status" else runtime.work.status()
        label = "Worker foundation" if command == "worker status" else "Work intelligence"
        return (label + ": " + " ".join(f"{key}={value}" for key, value in values.items()))[:4000]
    if command == "worker list":
        records = runtime.refresh_workers()
        return ("Workers: " + "; ".join(f"{item.worker_id}:{item.status.value}:execution={_yes(item.execution_enabled)}" for item in records))[:6000]
    if command in {"worker show", "worker health"}:
        worker_id = args[0] if args else ""
        adapter = runtime.registry.adapter(worker_id)
        if adapter is None:
            return "Worker not found."
        item = adapter.health() if command == "worker health" else runtime.registry.get(worker_id)
        if item is None:
            return "Worker not found."
        return (
            f"Worker {item.worker_id}: status={item.status.value} version={item.detected_version or 'unknown'} "
            f"source={item.discovery_source} adapter={item.adapter_type} workspaces={','.join(mode.value for mode in item.workspace_modes)} "
            f"configured={_yes(item.configured)} authenticated={_yes(item.authenticated)} healthy={_yes(item.healthy)} "
            f"execution={_yes(item.execution_enabled)} approval={_yes(item.approval_required)} authority={item.authority} reason={item.health_reason}"
        )[:4000]
    if command == "worker inventory":
        runtime.refresh_workers(health=True)
        return runtime.registry.inventory_json()[:12_000]
    if command in {"worker models", "worker model-refresh"}:
        if command == "worker model-refresh":
            runtime.refresh_models()
        models = runtime.models.list_models(args[0] if args else "")
        alias = runtime.models.alias("ox-alpha")
        body = "; ".join(f"{item.model_id}:status={item.status}:cost={item.cost_class}:free={item.free if item.free is not None else 'unknown'}:temporary={_yes(item.temporary)}" for item in models)
        return (f"Dynamic models: count={len(models)} {body or 'none'}; ox-alpha={alias.status if alias else 'unresolved'}")[:8000]
    if command == "worker providers":
        return ("Worker providers: " + "; ".join(f"{item.provider_id}:{item.status}:locality={item.locality}:enabled={_yes(item.enabled)}:cost={item.cost_class}" for item in runtime.providers.list()))[:7000]
    if command in {"worker route", "worker select"}:
        if not args:
            return "Usage: worker route <task> [local_only|private_hybrid|normal_hybrid|cloud_max]"
        mode = RoutingMode.LOCAL_ONLY
        if args[-1] in {item.value for item in RoutingMode}:
            mode = RoutingMode(args[-1])
            task = " ".join(args[:-1])
        else:
            task = " ".join(args)
        decision = runtime.route(RouteRequest(task, mode, independent_review=True))
        return (
            f"Worker route: status={decision.status} worker={decision.worker_id or 'none'} provider={decision.provider_id or 'none'} "
            f"model={decision.model_id or 'none'} reviewer={decision.reviewer_worker_id or 'none'} approval={_yes(decision.approval_required)} "
            f"mode={decision.execution_mode} fallbacks={','.join(decision.fallback_worker_ids) or 'none'} reason={decision.reason}"
        )[:4000]
    if command == "worker task-plan":
        if len(args) < 2:
            return "Usage: worker task-plan <worker_id> <objective>"
        task = WorkerTask(" ".join(args[1:]), args[0])
        adapter = runtime.registry.adapter(args[0])
        if adapter is None:
            return "Worker not found; no task was started."
        result = adapter.start_task(task)
        return f"Worker task {result.task_id}: worker={result.worker_id} status={result.status.value} summary={result.summary}"[:4000]
    if command == "work plan":
        if not args:
            return "Usage: work plan <goal>"
        goal, task, decision = runtime.plan_goal(" ".join(args))
        return f"Work plan: goal={goal.goal_id} task={task.task_id} owner={task.owner_worker_id} route={decision.status} authority=coordination_only approval_bypass=no"[:4000]
    if command == "work show":
        ref = args[0] if args else ""
        task = runtime.work.tasks.get(ref)
        if task:
            return f"Task {task.task_id}: status={task.status.value} owner={task.owner_worker_id} dependencies={','.join(task.dependencies) or 'none'} risk={task.risk} timeout={task.timeout_seconds}s"
        goal = runtime.work.goals.get(ref)
        return "Work item not found." if goal is None else f"Goal {goal.goal_id}: status={goal.status} criteria={len(goal.success_criteria)}"
    if command == "work graph":
        session = args[0] if args else "default"
        ids = sorted(runtime.work.sessions.get(session, set()))[:32]
        return ("Work graph: " + ("; ".join(f"{item}:{','.join(runtime.work.tasks[item].dependencies) or 'root'}" for item in ids) or "none"))[:5000]
    if command == "work worktree-plan":
        if len(args) < 2:
            return "Usage: work worktree-plan <task_id> <title>"
        plan = runtime.worktrees.plan(args[0], " ".join(args[1:]))
        return f"Worktree plan: task={plan.task_id} branch={plan.branch_name} workspace={plan.workspace_reference} status={plan.status} approval=yes auto_merge=no cleanup={plan.cleanup_policy}"
    if command == "work context":
        summary = runtime.context.summary(args[0] if args else "default")
        return "Work context: " + " ".join(f"{key}={value}" for key, value in summary.items()) + " payloads=not_exposed"
    if command == "work messages":
        values = runtime.work.messages[-20:]
        return ("Work messages: " + (", ".join(f"{item.message_id}:{item.kind.value}:{item.trust}" for item in values) or "none"))[:4000]
    return "Worker command unavailable. No external action was performed."
