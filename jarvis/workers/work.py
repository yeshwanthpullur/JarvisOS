"""Bounded goal/work records, DAG lifecycle, messages, and status persistence."""

from __future__ import annotations

from dataclasses import asdict, replace
from datetime import UTC, datetime
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import RLock
from typing import Callable

from .models import (
    AgentRun,
    Approval,
    Evidence,
    Goal,
    MessageKind,
    Milestone,
    Project,
    Result,
    Review,
    StructuredMessage,
    Subtask,
    Task,
    WorkerTaskStatus,
    WorkRuntimeLimits,
    bounded,
)


TERMINAL = {
    WorkerTaskStatus.COMPLETED,
    WorkerTaskStatus.CANCELLED,
    WorkerTaskStatus.TIMED_OUT,
    WorkerTaskStatus.FAILED,
    WorkerTaskStatus.BLOCKED,
}


class WorkStateStore:
    """Optional bounded metadata persistence; objectives and private content are omitted."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path

    def save(self, manager: "GoalWorkManager") -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "authority": "coordination_only",
            "goals": [{"goal_id": item.goal_id, "status": item.status} for item in manager.goals.values()],
            "tasks": [
                {
                    "task_id": item.task_id,
                    "owner_worker_id": item.owner_worker_id,
                    "dependencies": item.dependencies,
                    "status": item.status.value,
                    "risk": item.risk,
                    "session_id": next((session_id for session_id, task_ids in manager.sessions.items() if item.task_id in task_ids), "default"),
                }
                for item in manager.tasks.values()
            ],
        }
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        temporary.replace(self.path)

    def load(self) -> dict[str, object]:
        if self.path is None or not self.path.is_file():
            return {"goals": [], "tasks": []}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {"goals": [], "tasks": []}
        if payload.get("schema_version") != 1 or payload.get("authority") != "coordination_only":
            return {"goals": [], "tasks": []}
        return {
            "goals": tuple(payload.get("goals", ()))[:64],
            "tasks": tuple(payload.get("tasks", ()))[:64],
        }


class GoalWorkManager:
    def __init__(self, limits: WorkRuntimeLimits | None = None, store: WorkStateStore | None = None) -> None:
        self.limits = limits or WorkRuntimeLimits()
        self.store = store or WorkStateStore()
        self.goals: dict[str, Goal] = {}
        self.projects: dict[str, Project] = {}
        self.milestones: dict[str, Milestone] = {}
        self.tasks: dict[str, Task] = {}
        self.subtasks: dict[str, Subtask] = {}
        self.runs: dict[str, AgentRun] = {}
        self.reviews: dict[str, Review] = {}
        self.approvals: dict[str, Approval] = {}
        self.evidence: dict[str, Evidence] = {}
        self.results: dict[str, Result] = {}
        self.messages: list[StructuredMessage] = []
        self.sessions: dict[str, set[str]] = {}
        self.started_at: dict[str, datetime] = {}
        self._lock = RLock()
        self._restore()

    def _restore(self) -> None:
        payload = self.store.load()
        for value in payload.get("goals", ()):
            if not isinstance(value, dict):
                continue
            goal_id = bounded(value.get("goal_id"), 80)
            if goal_id:
                self.goals[goal_id] = Goal("[retained metadata]", (), goal_id=goal_id, status=bounded(value.get("status"), 40) or "planned")
        for value in payload.get("tasks", ()):
            if not isinstance(value, dict):
                continue
            try:
                task = Task(
                    "[retained metadata]",
                    bounded(value.get("owner_worker_id"), 80),
                    tuple(bounded(item, 80) for item in value.get("dependencies", ())[:16]),
                    task_id=bounded(value.get("task_id"), 80),
                    status=WorkerTaskStatus(str(value.get("status", "queued"))),
                    risk=bounded(value.get("risk"), 40),
                )
            except (TypeError, ValueError):
                continue
            if not task.task_id or not task.owner_worker_id:
                continue
            self.tasks[task.task_id] = task
            session_id = bounded(value.get("session_id"), 80) or "default"
            self.sessions.setdefault(session_id, set()).add(task.task_id)

    def create_goal(self, title: str, success_criteria: tuple[str, ...]) -> Goal:
        goal = Goal(bounded(title, 300), tuple(bounded(item, 300) for item in success_criteria[:16]))
        self.goals[goal.goal_id] = goal
        self.store.save(self)
        return goal

    def add_project(self, project: Project) -> None:
        self.projects[project.project_id] = project

    def add_milestone(self, milestone: Milestone) -> None:
        self.milestones[milestone.milestone_id] = milestone

    def add_task(self, task: Task, session_id: str = "default") -> None:
        with self._lock:
            if len(self.tasks) >= self.limits.max_tasks:
                raise ValueError("work_task_limit_exceeded")
            if task.task_id in self.tasks:
                raise ValueError("duplicate_work_task")
            self.tasks[task.task_id] = task
            self.sessions.setdefault(session_id, set()).add(task.task_id)
            try:
                self.validate_dag(session_id)
            except ValueError:
                self.tasks.pop(task.task_id, None)
                self.sessions[session_id].discard(task.task_id)
                raise
            self.store.save(self)

    def validate_dag(self, session_id: str = "default") -> bool:
        ids = self.sessions.get(session_id, set())
        for task_id in ids:
            task = self.tasks[task_id]
            if task_id in task.dependencies or any(dep not in ids for dep in task.dependencies):
                raise ValueError("invalid_work_dependency")
        visiting: set[str] = set()
        complete: set[str] = set()

        def visit(task_id: str) -> None:
            if task_id in visiting:
                raise ValueError("work_cycle_detected")
            if task_id in complete:
                return
            visiting.add(task_id)
            for dependency in self.tasks[task_id].dependencies:
                visit(dependency)
            visiting.remove(task_id)
            complete.add(task_id)

        for task_id in ids:
            visit(task_id)
        return True

    def ready_tasks(self, session_id: str = "default") -> tuple[Task, ...]:
        ids = self.sessions.get(session_id, set())
        active = sum(self.tasks[item].status is WorkerTaskStatus.RUNNING for item in ids)
        slots = max(0, self.limits.max_parallel_tasks - active)
        ready = []
        for task_id in sorted(ids):
            task = self.tasks[task_id]
            if task.status not in {WorkerTaskStatus.QUEUED, WorkerTaskStatus.PLANNING, WorkerTaskStatus.PLANNED, WorkerTaskStatus.READY, WorkerTaskStatus.RETRYING}:
                continue
            dependencies = tuple(self.tasks[dep] for dep in task.dependencies)
            if any(dep.status in {WorkerTaskStatus.FAILED, WorkerTaskStatus.BLOCKED, WorkerTaskStatus.CANCELLED, WorkerTaskStatus.TIMED_OUT} for dep in dependencies):
                self.tasks[task_id] = replace(task, status=WorkerTaskStatus.BLOCKED)
                continue
            if all(dep.status is WorkerTaskStatus.COMPLETED for dep in dependencies):
                ready.append(task)
        return tuple(ready[:slots])

    def mark(self, task_id: str, status: WorkerTaskStatus) -> Task:
        task = self.tasks[task_id]
        allowed = {
            WorkerTaskStatus.QUEUED: {WorkerTaskStatus.PLANNING, WorkerTaskStatus.READY, WorkerTaskStatus.RUNNING, WorkerTaskStatus.BLOCKED, WorkerTaskStatus.CANCELLED},
            WorkerTaskStatus.PLANNING: {WorkerTaskStatus.PLANNED, WorkerTaskStatus.READY, WorkerTaskStatus.BLOCKED, WorkerTaskStatus.CANCELLED},
            WorkerTaskStatus.PLANNED: {WorkerTaskStatus.RUNNING, WorkerTaskStatus.BLOCKED, WorkerTaskStatus.CANCELLED},
            WorkerTaskStatus.READY: {WorkerTaskStatus.RUNNING, WorkerTaskStatus.CANCELLED},
            WorkerTaskStatus.RUNNING: {WorkerTaskStatus.WAITING, WorkerTaskStatus.REVIEWING, WorkerTaskStatus.COMPLETED, WorkerTaskStatus.CANCELLED, WorkerTaskStatus.TIMED_OUT, WorkerTaskStatus.FAILED, WorkerTaskStatus.RETRYING},
            WorkerTaskStatus.WAITING: {WorkerTaskStatus.RUNNING, WorkerTaskStatus.CANCELLED, WorkerTaskStatus.TIMED_OUT},
            WorkerTaskStatus.REVIEWING: {WorkerTaskStatus.COMPLETED, WorkerTaskStatus.FAILED, WorkerTaskStatus.RETRYING},
            WorkerTaskStatus.RETRYING: {WorkerTaskStatus.RUNNING, WorkerTaskStatus.FAILED, WorkerTaskStatus.CANCELLED},
            WorkerTaskStatus.CANCELLED: {WorkerTaskStatus.QUEUED},
        }
        if status not in allowed.get(task.status, set()):
            raise ValueError("invalid_work_state_transition")
        task = replace(task, status=status)
        self.tasks[task_id] = task
        if status is WorkerTaskStatus.RUNNING:
            self.started_at[task_id] = datetime.now(UTC)
        self.store.save(self)
        return task

    def expire_timeouts(self, current: datetime | None = None) -> tuple[str, ...]:
        current = current or datetime.now(UTC)
        expired = []
        for task_id, started in tuple(self.started_at.items()):
            task = self.tasks.get(task_id)
            if task and task.status in {WorkerTaskStatus.RUNNING, WorkerTaskStatus.WAITING} and (current - started).total_seconds() > task.timeout_seconds:
                self.tasks[task_id] = replace(task, status=WorkerTaskStatus.TIMED_OUT)
                expired.append(task_id)
        if expired:
            self.store.save(self)
        return tuple(expired)

    def cancel(self, task_id: str) -> bool:
        task = self.tasks.get(task_id)
        if task is None or task.status in TERMINAL:
            return False
        self.mark(task_id, WorkerTaskStatus.CANCELLED)
        return True

    def resume(self, task_id: str) -> bool:
        task = self.tasks.get(task_id)
        if task is None or task.status is not WorkerTaskStatus.CANCELLED:
            return False
        self.mark(task_id, WorkerTaskStatus.QUEUED)
        return True

    def send(self, message: StructuredMessage) -> StructuredMessage:
        if message.task_id not in self.tasks:
            raise ValueError("unknown_message_task")
        if message.task_id not in self.sessions.get(message.session_id, set()):
            raise ValueError("cross_session_message_blocked")
        self.messages = (self.messages + [message])[-self.limits.max_messages :]
        return message

    def completion_claim(self, session_id: str, task_id: str, sender: str, evidence_refs: tuple[str, ...]) -> StructuredMessage:
        if not evidence_refs:
            raise ValueError("completion_claim_requires_evidence")
        return self.send(StructuredMessage(session_id, task_id, sender, "prime_agent", MessageKind.COMPLETION_CLAIM, f"evidence:{','.join(evidence_refs[:8])}", "unverified", evidence_refs=evidence_refs[:16]))

    def simulate_parallel(self, session_id: str, handlers: dict[str, Callable[[Task], Result]]) -> tuple[Result, ...]:
        """Run supplied in-process test handlers with bounded concurrency and isolated results."""
        ready = tuple(task for task in self.ready_tasks(session_id) if task.parallel_safe)
        if not ready:
            return ()
        outputs: list[Result] = []
        with ThreadPoolExecutor(max_workers=self.limits.max_parallel_tasks, thread_name_prefix="jarvis-work-sim") as pool:
            futures = {pool.submit(handlers[task.owner_worker_id], task): task for task in ready if task.owner_worker_id in handlers}
            for future in as_completed(futures):
                task = futures[future]
                try:
                    result = future.result(timeout=task.timeout_seconds)
                except Exception as exc:
                    result = Result(task.task_id, WorkerTaskStatus.FAILED, summary=bounded(f"{type(exc).__name__}: simulated worker failed", 300))
                outputs.append(result)
        return tuple(outputs)

    def status(self) -> dict[str, object]:
        values = tuple(self.tasks.values())
        return {
            "authority": "coordination_only",
            "goals": len(self.goals),
            "tasks": len(values),
            "running": sum(item.status is WorkerTaskStatus.RUNNING for item in values),
            "completed": sum(item.status is WorkerTaskStatus.COMPLETED for item in values),
            "blocked": sum(item.status is WorkerTaskStatus.BLOCKED for item in values),
            "messages": len(self.messages),
            "max_parallel": self.limits.max_parallel_tasks,
            "approval_bypass": False,
            "broker_bypass": False,
        }
