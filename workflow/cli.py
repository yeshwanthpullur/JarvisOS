"""Bounded CLI rendering for the workflow runtime."""

from __future__ import annotations

from dataclasses import asdict

from workflow.runtime import WorkflowRuntime


def _line_map(values: dict[str, object]) -> str:
    return " ".join(f"{key}={value}" for key, value in values.items())[:4000]


def render_workflow_command(runtime: WorkflowRuntime, command: str, arguments: tuple[str, ...]) -> str:
    try:
        if command == "workflow status":
            return "Workflow status: " + _line_map(runtime.status())
        if command == "workflow list":
            items = [runtime.safe_snapshot(item.workflow_id) for item in list(runtime.workflows.values())[-25:]]
            return "Workflow list: " + ("; ".join(_line_map(item) for item in items) if items else "none")
        if command in {"workflow show", "workflow graph", "workflow trace", "workflow events", "workflow checkpoints"}:
            if not arguments:
                return "Workflow error: workflow_id_required"
            workflow_id = arguments[0]
            if command == "workflow show":
                return "Workflow: " + _line_map(runtime.safe_snapshot(workflow_id))
            if command == "workflow graph":
                return "Workflow graph: " + _line_map(runtime.graph(workflow_id))
            if command == "workflow trace":
                events = [event for event in runtime.events if event.workflow_id == workflow_id][-50:]
                return "Workflow trace: " + ("; ".join(f"{event.sequence}:{event.event_type}:{event.result}" for event in events) or "none")
            if command == "workflow events":
                events = [event for event in runtime.events if event.workflow_id == workflow_id][-50:]
                return "Workflow events: " + ("; ".join(f"{event.event_type}:{event.result}" for event in events) or "none")
            checkpoints = [item for item in runtime.checkpoints.values() if item.workflow_id == workflow_id][-25:]
            return "Workflow checkpoints: " + ("; ".join(f"{item.checkpoint_id}:{item.step_index}" for item in checkpoints) or "none")
        if command == "workflow checkpoint-show":
            checkpoint = runtime.checkpoints.get(arguments[0] if arguments else "")
            return "Workflow checkpoint: " + (_line_map(asdict(checkpoint)) if checkpoint else "not_found")
        if command in {"workflow pause", "workflow resume", "workflow cancel"}:
            if not arguments:
                return "Workflow error: workflow_id_required"
            workflow = getattr(runtime, command.split()[1])(arguments[0])
            return f"Workflow {command.split()[1]}: workflow_id={workflow.workflow_id} state={workflow.state.value}"
        if command == "workflow simulate":
            return "Workflow simulation: " + _line_map(runtime.simulate(" ".join(arguments)))
        if command == "workflow health":
            return "Workflow health: " + _line_map(runtime.health())
        if command == "workflow metrics":
            return "Workflow metrics: " + _line_map(runtime.metrics)
        if command == "workflow cleanup-plan":
            return "Workflow cleanup plan: " + _line_map(runtime.cleanup_plan())
        if command == "workflow artifact-list":
            items = list(runtime.artifacts.values())[-25:]
            return "Workflow artifacts: " + ("; ".join(f"{item.artifact_id}:{item.artifact_type}:{item.storage_class}" for item in items) or "none")
        if command == "workflow artifact-show":
            item = runtime.artifacts.get(arguments[0] if arguments else "")
            return "Workflow artifact: " + (_line_map(asdict(item)) if item else "not_found")
        return "Workflow commands: status, list, show, graph, trace, events, checkpoints, checkpoint-show, pause, resume, cancel, simulate, health, metrics, cleanup-plan, artifact-list, artifact-show."
    except (ValueError, IndexError) as exc:
        return f"Workflow error: {exc}"
