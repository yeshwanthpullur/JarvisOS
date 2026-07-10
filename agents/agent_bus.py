"""Agent communication bus."""

from __future__ import annotations

import logging
from collections import deque
from typing import Callable

from agents.agent_events import AgentEvent
from agents.agent_message import AgentMessage, AgentMessageStatus


class AgentBus:
    """Internal message and event backbone for agents."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._message_handlers: dict[str, Callable[[AgentMessage], None]] = {}
        self._event_handlers: dict[str, list[Callable[[AgentEvent], None]]] = {}
        self._message_queue: deque[AgentMessage] = deque()
        self._message_history: list[AgentMessage] = []
        self._event_history: list[AgentEvent] = []
        self._logger = logger or logging.getLogger(__name__)
        self.initialized = True

    def register_message_handler(self, agent_id: str, handler: Callable[[AgentMessage], None]) -> None:
        """Register a handler for an agent."""
        self._message_handlers[agent_id] = handler

    def route_message(self, message: AgentMessage) -> bool:
        """Route a message to a registered handler."""
        self._message_queue.append(message)
        handler = self._message_handlers.get(message.receiver)
        if handler is None:
            message.status = AgentMessageStatus.FAILED
            self._message_history.append(message)
            return False
        message.status = AgentMessageStatus.ROUTED
        handler(message)
        message.status = AgentMessageStatus.DELIVERED
        self._message_history.append(message)
        return True

    def subscribe(self, category: str, handler: Callable[[AgentEvent], None]) -> None:
        """Subscribe to event category."""
        self._event_handlers.setdefault(category, []).append(handler)

    def publish(self, event: AgentEvent) -> None:
        """Publish an event."""
        self._event_history.append(event)
        for handler in self._event_handlers.get(event.category.value, ()):
            handler(event)

    def broadcast_event(self, event: AgentEvent) -> None:
        """Broadcast an event."""
        self.publish(event)

    def message_history(self) -> tuple[AgentMessage, ...]:
        """Return message history."""
        return tuple(self._message_history)

    def event_history(self) -> tuple[AgentEvent, ...]:
        """Return event history."""
        return tuple(self._event_history)
