"""Task Manager for the JARVIS OS Task Engine."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from tasks.priority import TaskPriority
from tasks.status import TERMINAL_STATUSES, TaskStatus
from tasks.task import Task, TaskCreate, create_task_model, utc_now
from tasks.task_executor import TaskExecutor
from tasks.task_history import TaskHistory
from tasks.task_queue import TaskQueue
from tasks.task_scheduler import TaskScheduler


@dataclass(frozen=True, slots=True)
class TaskEngineStatistics:
    """Operational statistics for the in-memory Task Engine."""

    total_tasks: int
    queued_tasks: int
    history_count: int


class TaskManager:
    """Coordinates task lifecycle, queueing, scheduling, and history.

    The manager does not execute task work. It only owns task architecture and
    lifecycle state so future agents can create tasks instead of performing work
    directly.
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._tasks: dict[str, Task] = {}
        self.queue = TaskQueue(logger=self._logger)
        self.history = TaskHistory(logger=self._logger)
        self.executor = TaskExecutor(logger=self._logger)
        self.scheduler = TaskScheduler(logger=self._logger)
        self.initialized = False

    def initialize(self) -> None:
        """Initialize Task Engine collaborators."""
        self.executor.initialize()
        self.scheduler.initialize()
        self.initialized = True
        self._logger.info("task_manager_initialized")

    def create_task(
        self,
        name: str,
        description: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        dependencies: tuple[str, ...] = (),
        assigned_agent: str | None = None,
        related_memories: tuple[str, ...] = (),
        input_files: tuple[Path, ...] = (),
        metadata: dict[str, object] | None = None,
        queue_mode: str = "priority",
    ) -> Task:
        """Create a task and enqueue it."""
        self._ensure_initialized()
        task = create_task_model(
            TaskCreate(
                name=name,
                description=description,
                priority=priority,
                dependencies=dependencies,
                assigned_agent=assigned_agent,
                related_memories=related_memories,
                input_files=input_files,
                metadata=dict(metadata or {}),
            )
        )
        self._tasks[task.task_id] = task
        self._queue_task(task, queue_mode=queue_mode)
        self._logger.info("task_created task_id=%s name=%s", task.task_id, task.name)
        return task

    def delete_task(self, task_id: str) -> bool:
        """Delete a task from active state and queue."""
        self._ensure_initialized()
        task = self._tasks.pop(task_id, None)
        self.queue.remove(task_id)
        deleted = task is not None
        self._logger.info("task_deleted task_id=%s deleted=%s", task_id, deleted)
        return deleted

    def pause_task(self, task_id: str) -> Task | None:
        """Pause a non-terminal task."""
        self.queue.remove(task_id)
        return self._transition(task_id, TaskStatus.PAUSED, "Task paused.")

    def resume_task(self, task_id: str, queue_mode: str = "priority") -> Task | None:
        """Resume a paused task by queueing it again."""
        task = self._tasks.get(task_id)
        if task is None or task.status is not TaskStatus.PAUSED:
            self._logger.warning("task_resume_rejected task_id=%s", task_id)
            return None
        self._queue_task(task, queue_mode=queue_mode)
        task.add_log("Task resumed.")
        self._logger.info("task_resumed task_id=%s", task_id)
        return task

    def retry_task(self, task_id: str, queue_mode: str = "priority") -> Task | None:
        """Retry a failed task by incrementing retry count and queueing it."""
        task = self._tasks.get(task_id)
        if task is None or task.status is not TaskStatus.FAILED:
            self._logger.warning("task_retry_rejected task_id=%s", task_id)
            return None
        task.retry_count += 1
        task.completed_at = None
        self._queue_task(task, queue_mode=queue_mode)
        task.add_log("Task retry queued.")
        self._logger.info("task_retry_queued task_id=%s retry_count=%s", task_id, task.retry_count)
        return task

    def cancel_task(self, task_id: str) -> Task | None:
        """Cancel a task and record it in history."""
        self.queue.remove(task_id)
        return self._transition(task_id, TaskStatus.CANCELLED, "Task cancelled.")

    def complete_task(self, task_id: str) -> Task | None:
        """Mark a task completed without executing work."""
        self.queue.remove(task_id)
        return self._transition(task_id, TaskStatus.COMPLETED, "Task completed.")

    def fail_task(self, task_id: str) -> Task | None:
        """Mark a task failed without executing work."""
        self.queue.remove(task_id)
        return self._transition(task_id, TaskStatus.FAILED, "Task failed.")

    def list_tasks(self, include_history: bool = False) -> tuple[Task, ...]:
        """List active tasks and optionally historical terminal tasks."""
        self._ensure_initialized()
        tasks = tuple(self._tasks.values())
        if include_history:
            return (*tasks, *self.history.list_tasks())
        return tasks

    def search_tasks(self, query: str) -> tuple[Task, ...]:
        """Search active and historical tasks by text fields."""
        self._ensure_initialized()
        normalized = query.strip().lower()
        candidates = (*self._tasks.values(), *self.history.list_tasks())
        results = tuple(
            task
            for task in candidates
            if normalized in task.name.lower()
            or normalized in task.description.lower()
            or normalized in task.task_id.lower()
        )
        self._logger.info("task_search query=%s count=%s", query, len(results))
        return results

    def get_task(self, task_id: str) -> Task | None:
        """Return a task from active state or history."""
        self._ensure_initialized()
        return self._tasks.get(task_id) or self.history.get(task_id)

    def statistics(self) -> TaskEngineStatistics:
        """Return Task Engine statistics."""
        self._ensure_initialized()
        return TaskEngineStatistics(
            total_tasks=len(self._tasks),
            queued_tasks=len(self.queue),
            history_count=self.history.count(),
        )

    def _queue_task(self, task: Task, queue_mode: str) -> None:
        task.status = TaskStatus.QUEUED
        task.add_log(f"Task queued using {queue_mode} mode.")
        if queue_mode == "fifo":
            self.queue.enqueue_fifo(task)
        elif queue_mode == "priority":
            self.queue.enqueue_priority(task)
        else:
            raise ValueError("queue_mode must be either 'fifo' or 'priority'.")

    def _transition(self, task_id: str, status: TaskStatus, message: str) -> Task | None:
        self._ensure_initialized()
        task = self._tasks.get(task_id)
        if task is None:
            self._logger.warning("task_transition_missing task_id=%s status=%s", task_id, status.value)
            return None
        if task.status in TERMINAL_STATUSES:
            self._logger.warning("task_transition_terminal task_id=%s status=%s", task_id, task.status.value)
            return None

        task.status = status
        if status is TaskStatus.RUNNING and task.started_at is None:
            task.started_at = utc_now()
        if status in TERMINAL_STATUSES:
            task.completed_at = utc_now()
        task.add_log(message)
        if status in TERMINAL_STATUSES:
            self.history.record(task)
        self._logger.info("task_status_changed task_id=%s status=%s", task_id, status.value)
        return task

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("TaskManager must be initialized before use.")
