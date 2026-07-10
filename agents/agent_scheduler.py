"""Agent scheduler architecture."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from datetime import datetime
from itertools import count
from typing import Any


@dataclass(frozen=True, slots=True)
class ScheduledAgentWork:
    """Scheduled agent work metadata."""

    agent_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    priority: int = 100
    run_at: datetime | None = None
    retry_count: int = 0
    timeout_seconds: int | None = None


class AgentScheduler:
    """Maintains execution, waiting, and priority queues without executing work."""

    def __init__(self) -> None:
        self._priority_queue: list[tuple[int, int, ScheduledAgentWork]] = []
        self._waiting: list[ScheduledAgentWork] = []
        self._sequence = count()
        self.paused = False
        self.initialized = True

    def schedule(self, work: ScheduledAgentWork) -> None:
        """Schedule work by priority."""
        heapq.heappush(self._priority_queue, (work.priority, next(self._sequence), work))

    def schedule_waiting(self, work: ScheduledAgentWork) -> None:
        """Schedule delayed or waiting work."""
        self._waiting.append(work)

    def next_work(self) -> ScheduledAgentWork | None:
        """Return next scheduled work without executing it."""
        if self.paused or not self._priority_queue:
            return None
        return heapq.heappop(self._priority_queue)[2]

    def cancel(self, agent_id: str) -> None:
        """Remove queued work for an agent."""
        self._priority_queue = [item for item in self._priority_queue if item[2].agent_id != agent_id]
        heapq.heapify(self._priority_queue)

    def pause(self) -> None:
        """Pause scheduling."""
        self.paused = True

    def resume(self) -> None:
        """Resume scheduling."""
        self.paused = False

    def queue_length(self) -> int:
        """Return total queued work."""
        return len(self._priority_queue) + len(self._waiting)
