"""In-memory task queues for JARVIS OS."""

from __future__ import annotations

import heapq
import logging
from collections import deque
from itertools import count

from tasks.task import Task


class TaskQueue:
    """Queue facade supporting FIFO and priority ordering.

    The queue stores task IDs only. Task state remains owned by TaskManager.
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._fifo: deque[str] = deque()
        self._priority: list[tuple[int, int, str]] = []
        self._sequence = count()
        self._queued_ids: set[str] = set()
        self._logger = logger or logging.getLogger(__name__)

    def enqueue_fifo(self, task: Task) -> None:
        """Queue a task using FIFO order."""
        if task.task_id in self._queued_ids:
            return
        self._fifo.append(task.task_id)
        self._queued_ids.add(task.task_id)
        self._logger.info("task_queued mode=fifo task_id=%s", task.task_id)

    def enqueue_priority(self, task: Task) -> None:
        """Queue a task using priority ordering."""
        if task.task_id in self._queued_ids:
            return
        heapq.heappush(self._priority, (int(task.priority), next(self._sequence), task.task_id))
        self._queued_ids.add(task.task_id)
        self._logger.info("task_queued mode=priority task_id=%s", task.task_id)

    def dequeue_fifo(self) -> str | None:
        """Return the next FIFO task ID."""
        while self._fifo:
            task_id = self._fifo.popleft()
            if task_id in self._queued_ids:
                self._queued_ids.remove(task_id)
                return task_id
        return None

    def dequeue_priority(self) -> str | None:
        """Return the next priority task ID."""
        while self._priority:
            _, _, task_id = heapq.heappop(self._priority)
            if task_id in self._queued_ids:
                self._queued_ids.remove(task_id)
                return task_id
        return None

    def remove(self, task_id: str) -> None:
        """Remove a task ID from future queue results."""
        self._queued_ids.discard(task_id)
        self._logger.info("task_queue_removed task_id=%s", task_id)

    def __len__(self) -> int:
        """Return queued task count."""
        return len(self._queued_ids)

